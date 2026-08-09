from __future__ import annotations

import random
from typing import Any

from app.engine.export_formats import (
    draft_to_score,
    notes_payload,
    score_to_midi_base64,
    score_to_musicxml,
)
from app.engine.harmony import chord_pitches
from app.engine.rhythm import choose_rhythm_pattern, left_hand_for_bar
from app.engine.types import ChordEvent, NoteEvent, PieceDraft

SIMPLE_PROFILE = {
    "id": "simple",
    "personality_type": "neutral",
    "tempo_bpm_range": [62, 62],
    "rhythm_patterns": ["marcato_en_dos"],
    "articulation": {
        "staccato_level": "medium",
        "rubato_level": "low",
        "dynamic_contrast": "medium",
        "pause_frequency": "low",
    },
    "instrumentation_defaults": ["piano"],
}

# Relative mix + decoration bias by personality (teaching caricature, not archival fidelity)
PERSONALITY_MIX = {
    "neutral": {
        "decoration": 0.1,
        "volumes": {"piano_lh": 0.75, "piano_rh": 0.9, "bandoneon": 0.0, "strings": 0.0},
    },
    "rhythmic": {
        "decoration": 0.35,
        "volumes": {"piano_lh": 1.0, "piano_rh": 0.78, "bandoneon": 0.55, "strings": 0.3},
    },
    "lyrical": {
        "decoration": 0.55,
        "volumes": {"piano_lh": 0.55, "piano_rh": 0.85, "bandoneon": 1.0, "strings": 0.7},
    },
    "smooth_powerful": {
        "decoration": 0.25,
        "volumes": {"piano_lh": 0.95, "piano_rh": 0.7, "bandoneon": 0.45, "strings": 0.75},
    },
    "dramatic": {
        "decoration": 0.7,
        "volumes": {"piano_lh": 0.9, "piano_rh": 0.85, "bandoneon": 0.8, "strings": 0.85},
    },
}


def _level_to_01(level: str) -> float:
    return {"low": 0.25, "medium": 0.5, "high": 0.8, "very_high": 1.0}.get(level, 0.5)


def _bpm(profile: dict, rng: random.Random, skeleton: dict) -> float:
    if profile.get("id") == "simple":
        return float(skeleton.get("default_bpm", 64))
    lo, hi = profile.get("tempo_bpm_range", [60, 66])
    base = float(skeleton.get("default_bpm", 64))
    style = float(rng.randint(int(lo), int(hi)))
    if skeleton.get("dance_type") == "milonga":
        return max(style, base * 0.9)
    if skeleton.get("dance_type") == "vals":
        return (style + base) / 2
    return style


def _rhythm_for_dance(profile: dict, dance_type: str) -> str:
    if profile.get("id") == "simple":
        if dance_type == "vals":
            return "lyrical_phrasing"
        if dance_type == "milonga":
            return "milonga_habanera"
        return "marcato_en_dos"
    pattern = choose_rhythm_pattern(profile)
    if dance_type == "vals" and pattern.startswith("marcato_en_cuatro"):
        return "lyrical_phrasing"
    if dance_type == "milonga" and pattern in ("pesante", "yumba"):
        return "milonga_habanera"
    return pattern


def _seconds_per_beat(bpm: float) -> float:
    return 60.0 / bpm


def _mix_for(profile: dict) -> dict[str, Any]:
    ptype = profile.get("personality_type", "neutral")
    return PERSONALITY_MIX.get(ptype, PERSONALITY_MIX["neutral"])


def _default_instruments(profile: dict) -> dict[str, bool]:
    defaults = set(profile.get("instrumentation_defaults") or ["piano"])
    return {
        "piano": True,
        "bandoneon": "bandoneon" in defaults and profile.get("id") != "simple",
        "strings": "strings" in defaults and profile.get("id") != "simple",
    }


def _apply_vel(base: int, track_vol: float) -> int:
    return max(1, min(127, int(base * track_vol)))


def _decorate_melody(
    rng: random.Random,
    melody: list[dict],
    *,
    decoration: float,
    spb: float,
    staccato: str,
) -> list[NoteEvent]:
    notes: list[NoteEvent] = []
    for m in melody:
        start = float(m["start_beat"]) * spb
        dur = float(m["duration_beats"]) * spb
        pitch = int(m["pitch"])
        if staccato == "high":
            dur *= 0.55
        elif staccato == "low":
            dur *= 1.1
        vel = 82 if staccato != "low" else 74
        notes.append(
            NoteEvent(pitch, start, max(0.05, dur), vel, "piano_rh")
        )
        # grace / turn decorations
        if rng.random() < decoration * 0.65:
            grace_pitch = pitch + rng.choice([-1, 1, 2, -2])
            notes.append(
                NoteEvent(
                    grace_pitch,
                    max(0.0, start - spb * 0.12),
                    spb * 0.1,
                    max(50, vel - 18),
                    "piano_rh",
                )
            )
        if rng.random() < decoration * 0.35:
            # mordent-like neighbor
            notes.append(
                NoteEvent(pitch + 1, start + dur * 0.35, dur * 0.2, vel - 10, "piano_rh")
            )
    return notes


def _bandoneon_line(
    rng: random.Random,
    melody: list[dict],
    *,
    spb: float,
    decoration: float,
    lyrical: bool,
) -> list[NoteEvent]:
    notes: list[NoteEvent] = []
    for i, m in enumerate(melody):
        # Often double melody an octave below / unison with lag
        pitch = int(m["pitch"]) - (12 if lyrical else 0)
        start = float(m["start_beat"]) * spb + (spb * 0.05 if lyrical else 0)
        dur = float(m["duration_beats"]) * spb * (1.2 if lyrical else 0.9)
        if i % 3 == 2 and rng.random() < 0.4 + decoration * 0.3:
            continue  # leave air
        notes.append(NoteEvent(pitch, start, max(0.08, dur), 78, "bandoneon"))
        if rng.random() < decoration * 0.4:
            notes.append(
                NoteEvent(pitch + rng.choice([3, 4, 5]), start + dur * 0.5, dur * 0.4, 64, "bandoneon")
            )
    return notes


def _strings_pads(
    skeleton: dict,
    *,
    spb: float,
    tonic: int,
    mode: str,
    dramatic: bool,
) -> list[NoteEvent]:
    notes: list[NoteEvent] = []
    beats_per_bar = int(skeleton["beats_per_bar"])
    bar_len = beats_per_bar * spb
    for ch in skeleton["chords"]:
        bar = int(ch["bar"])
        # Hold every other bar for breathing, denser if dramatic
        if not dramatic and bar % 2 == 1:
            continue
        pitches = chord_pitches(tonic, mode, ch["symbol"], octave_shift=1)
        start = bar * bar_len
        dur = bar_len * (1.8 if dramatic and bar % 4 == 0 else 1.5)
        for p in pitches[:3]:
            notes.append(NoteEvent(p + 12, start, dur, 48 if not dramatic else 58, "strings"))
    return notes


def render_skeleton(
    skeleton: dict[str, Any],
    profile: dict,
    *,
    seed: int | None = None,
    instruments: dict[str, bool] | None = None,
    include_midi: bool = True,
    include_musicxml: bool = False,
) -> dict[str, Any]:
    seed = int(seed if seed is not None else skeleton.get("seed") or random.randint(1, 2_147_483_647))
    style_salt = sum(ord(c) for c in str(profile.get("id", "x")))
    rng = random.Random(seed ^ style_salt)

    bpm = _bpm(profile, rng, skeleton)
    spb = _seconds_per_beat(bpm)
    beats_per_bar = int(skeleton["beats_per_bar"])
    bar_len = beats_per_bar * spb
    time_signature = tuple(skeleton["time_signature"])
    rhythm = _rhythm_for_dance(profile, skeleton["dance_type"])
    articulation = profile.get("articulation", SIMPLE_PROFILE["articulation"])
    tonic = int(skeleton["tonic"])
    mode = skeleton["mode"]
    mix = _mix_for(profile)
    vols = dict(mix["volumes"])
    decoration = float(mix["decoration"])
    # Boost decoration from profile articulation contrast
    decoration = min(
        1.0,
        decoration * 0.6
        + 0.4 * _level_to_01(str(articulation.get("dynamic_contrast", "medium"))),
    )
    if profile.get("id") == "simple":
        decoration = 0.05

    enabled = _default_instruments(profile)
    if instruments:
        for k in ("piano", "bandoneon", "strings"):
            if k in instruments:
                enabled[k] = bool(instruments[k])

    # If user turns on a layer that personality mix muted, give it an audible floor
    for layer, floor in (("bandoneon", 0.55), ("strings", 0.5)):
        if enabled.get(layer) and vols.get(layer, 0) < 0.15:
            vols[layer] = floor

    notes: list[NoteEvent] = []
    chord_events: list[ChordEvent] = []

    if enabled.get("piano", True):
        for ch in skeleton["chords"]:
            bar = int(ch["bar"])
            symbol = ch["symbol"]
            pitches = chord_pitches(tonic, mode, symbol)
            bar_start = bar * bar_len
            chord_events.append(
                ChordEvent(bar=bar, symbol=symbol, start=bar_start, duration=bar_len)
            )
            lh = left_hand_for_bar(
                rhythm, bar, bar_start, bar_len, pitches, articulation
            )
            for n in lh:
                n.velocity = _apply_vel(n.velocity, vols.get("piano_lh", 0.8))
                notes.append(n)

        rh = _decorate_melody(
            rng,
            skeleton["melody"],
            decoration=decoration,
            spb=spb,
            staccato=str(articulation.get("staccato_level", "medium")),
        )
        for n in rh:
            if profile.get("id") == "simple":
                n.velocity = _apply_vel(74, vols.get("piano_rh", 0.9))
            else:
                n.velocity = _apply_vel(n.velocity, vols.get("piano_rh", 0.85))
            notes.append(n)
    else:
        for ch in skeleton["chords"]:
            bar = int(ch["bar"])
            chord_events.append(
                ChordEvent(
                    bar=bar,
                    symbol=ch["symbol"],
                    start=bar * bar_len,
                    duration=bar_len,
                )
            )

    if enabled.get("bandoneon"):
        lyrical = profile.get("personality_type") == "lyrical"
        bn = _bandoneon_line(
            rng,
            skeleton["melody"],
            spb=spb,
            decoration=decoration,
            lyrical=lyrical,
        )
        for n in bn:
            n.velocity = _apply_vel(n.velocity, vols.get("bandoneon", 0.7))
            notes.append(n)

    if enabled.get("strings"):
        st = _strings_pads(
            skeleton,
            spb=spb,
            tonic=tonic,
            mode=mode,
            dramatic=profile.get("personality_type") == "dramatic",
        )
        for n in st:
            n.velocity = _apply_vel(n.velocity, vols.get("strings", 0.6))
            notes.append(n)

    notes.sort(key=lambda n: (n.start, n.track, n.pitch))
    draft = PieceDraft(
        orchestra_id=profile["id"],
        seed=seed,
        bpm=bpm,
        key_name=skeleton["key"],
        mode=mode,
        time_signature=time_signature,  # type: ignore[arg-type]
        rhythm_pattern=rhythm,
        form=list(skeleton.get("form") or []),
        notes=notes,
        chords=chord_events,
        bars=int(skeleton["bars"]),
    )
    score = draft_to_score(draft)
    duration = draft.bars * bar_len
    payload: dict[str, Any] = {
        "orchestra_id": draft.orchestra_id,
        "skeleton_seed": skeleton.get("seed"),
        "seed": draft.seed,
        "bpm": draft.bpm,
        "key": draft.key_name,
        "mode": draft.mode,
        "dance_type": skeleton.get("dance_type"),
        "time_signature": list(draft.time_signature),
        "rhythm_pattern": draft.rhythm_pattern,
        "form": draft.form,
        "progression_id": skeleton.get("progression_id"),
        "melody_density": skeleton.get("melody_density"),
        "melody_variation": skeleton.get("melody_variation"),
        "decoration": round(decoration, 3),
        "volumes": vols,
        "instruments": enabled,
        "bars": draft.bars,
        "duration_seconds": round(duration, 2),
        "chords": [
            {
                "bar": c.bar,
                "symbol": c.symbol,
                "start": round(c.start, 4),
                "duration": round(c.duration, 4),
            }
            for c in draft.chords
        ],
        "notes": notes_payload(draft.notes),
    }
    if include_midi:
        payload["midi_base64"] = score_to_midi_base64(score)
    if include_musicxml:
        payload["musicxml"] = score_to_musicxml(score)
    return payload
