from __future__ import annotations

import random
from typing import Any

from app.engine.export_formats import (
    draft_to_score,
    notes_payload,
    score_to_midi_base64,
    score_to_musicxml,
)
from app.engine.catalog import DANCE_TYPES
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

# Relative mix — decoration is "chance of a phrase-end ornament", not per-note density
PERSONALITY_MIX = {
    "neutral": {
        "decoration": 0.15,
        "volumes": {"piano_lh": 0.75, "piano_rh": 0.9, "bandoneon": 0.0, "strings": 0.0},
    },
    "rhythmic": {
        "decoration": 0.35,
        "volumes": {"piano_lh": 1.0, "piano_rh": 0.78, "bandoneon": 0.5, "strings": 0.25},
    },
    "lyrical": {
        "decoration": 0.55,
        "volumes": {"piano_lh": 0.55, "piano_rh": 0.85, "bandoneon": 0.85, "strings": 0.65},
    },
    "smooth_powerful": {
        "decoration": 0.3,
        "volumes": {"piano_lh": 0.95, "piano_rh": 0.7, "bandoneon": 0.55, "strings": 0.7},
    },
    "dramatic": {
        "decoration": 0.65,
        "volumes": {"piano_lh": 0.9, "piano_rh": 0.85, "bandoneon": 0.7, "strings": 0.8},
    },
}


def _level_to_01(level: str) -> float:
    return {"low": 0.25, "medium": 0.5, "high": 0.8, "very_high": 1.0}.get(level, 0.5)


def _bpm(profile: dict, rng: random.Random, skeleton: dict) -> float:
    dance_type = skeleton.get("dance_type") or "tango"
    base = float(skeleton.get("default_bpm", DANCE_TYPES.get(dance_type, {}).get("default_bpm", 64)))
    # Dance tempo is authoritative for milonga/vals — orquesta ranges are tango-centric
    if dance_type == "milonga":
        return round(base * rng.uniform(0.96, 1.08), 1)
    if dance_type == "vals":
        return round(base * rng.uniform(0.95, 1.06), 1)
    if profile.get("id") == "simple":
        return base
    lo, hi = profile.get("tempo_bpm_range", [60, 66])
    return float(rng.randint(int(lo), int(hi)))


def _rhythm_for_dance(profile: dict, dance_type: str, rng: random.Random) -> str:
    """Dance type wins for milonga/vals skeletons — orquesta accents layer on top later."""
    dance = DANCE_TYPES.get(dance_type, DANCE_TYPES["tango"])
    if dance_type == "vals":
        return "vals_bass_chord"
    if dance_type == "milonga":
        if profile.get("id") != "simple" and rng.random() < 0.35:
            return str(dance.get("alt_rhythm") or "milonga_332")
        return str(dance.get("default_rhythm") or "milonga_habanera")
    if profile.get("id") == "simple":
        return str(dance.get("default_rhythm") or "marcato_en_dos")
    return choose_rhythm_pattern(profile)


def _articulation_for_dance(profile: dict, dance_type: str) -> dict:
    base = dict(profile.get("articulation", SIMPLE_PROFILE["articulation"]))
    if dance_type == "milonga":
        # Punchier, less rubato — earthy drive
        base["staccato_level"] = "high" if base.get("staccato_level") != "low" else "medium"
        base["rubato_level"] = "low"
        base["pause_frequency"] = "low"
    elif dance_type == "vals":
        # Flowing — soft 2–3, little chop
        base["staccato_level"] = "low"
        base["rubato_level"] = "medium" if profile.get("id") != "simple" else "low"
        base["pause_frequency"] = "low"
    return base


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


def _phrase_end_ornament(
    rng: random.Random,
    pitch: int,
    start: float,
    dur: float,
    spb: float,
    vel: int,
) -> list[NoteEvent]:
    """Sparse tango-ish cadential ornaments (grace from below, or short turn)."""
    kind = rng.choice(["grace_below", "grace_below", "turn"])
    out: list[NoteEvent] = []
    if kind == "grace_below":
        grace = pitch - rng.choice([1, 2])
        out.append(
            NoteEvent(
                grace,
                max(0.0, start - spb * 0.1),
                spb * 0.08,
                max(48, vel - 20),
                "piano_rh",
            )
        )
    else:
        # Upper neighbor → return (keep short; no mid-note clutter)
        upper = pitch + 1
        out.append(
            NoteEvent(upper, start + max(0.0, dur - spb * 0.22), spb * 0.08, vel - 12, "piano_rh")
        )
        out.append(
            NoteEvent(pitch, start + max(0.0, dur - spb * 0.12), spb * 0.1, vel - 8, "piano_rh")
        )
    return out


def _render_melody(
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
            dur *= 0.65
        elif staccato == "low":
            dur *= 1.05
        vel = 82 if staccato != "low" else 74
        notes.append(NoteEvent(pitch, start, max(0.05, dur), vel, "piano_rh"))

        # Ornaments ONLY at marked phrase endings (answers), never per-note spray
        if m.get("phrase_end") and m.get("phrase_role") == "answer":
            if rng.random() < decoration:
                notes.extend(
                    _phrase_end_ornament(rng, pitch, start, dur, spb, vel)
                )
    return notes


def _bandoneon_pads(
    skeleton: dict,
    *,
    spb: float,
    tonic: int,
    mode: str,
    lyrical: bool,
) -> list[NoteEvent]:
    """Long mid-register chord holds — harmonic backdrop, not melody doubling."""
    notes: list[NoteEvent] = []
    beats_per_bar = int(skeleton["beats_per_bar"])
    bar_len = beats_per_bar * spb
    chords = skeleton["chords"]
    i = 0
    while i < len(chords):
        ch = chords[i]
        symbol = ch["symbol"]
        # Hold through consecutive identical symbols (up to 2 bars)
        hold_bars = 1
        while (
            i + hold_bars < len(chords)
            and chords[i + hold_bars]["symbol"] == symbol
            and hold_bars < 2
        ):
            hold_bars += 1
        pitches = chord_pitches(tonic, mode, symbol, octave_shift=0)
        # Mid register: around C3–A4; take root + 3rd (and 5th if lyrical)
        mid = [p + 12 for p in pitches[: (3 if lyrical else 2)]]
        start = int(ch["bar"]) * bar_len
        dur = hold_bars * bar_len * (0.95 if lyrical else 0.88)
        for p in mid:
            notes.append(
                NoteEvent(p, start, dur, 62 if lyrical else 54, "bandoneon")
            )
        i += hold_bars
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
        if not dramatic and bar % 2 == 1:
            continue
        pitches = chord_pitches(tonic, mode, ch["symbol"], octave_shift=1)
        start = bar * bar_len
        dur = bar_len * (1.85 if dramatic and bar % 4 == 0 else 1.6)
        # Higher soft pad; avoid doubling melody register aggressively
        for p in pitches[:2]:
            notes.append(NoteEvent(p + 12, start, dur, 42 if not dramatic else 52, "strings"))
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
    dance_type = str(skeleton.get("dance_type") or "tango")
    rhythm = _rhythm_for_dance(profile, dance_type, rng)
    articulation = _articulation_for_dance(profile, dance_type)
    tonic = int(skeleton["tonic"])
    mode = skeleton["mode"]
    mix = _mix_for(profile)
    vols = dict(mix["volumes"])
    decoration = float(mix["decoration"])
    decoration = min(
        1.0,
        decoration * 0.75
        + 0.25 * _level_to_01(str(articulation.get("dynamic_contrast", "medium"))),
    )
    if profile.get("id") == "simple":
        decoration = 0.12
    if dance_type == "milonga":
        decoration *= 0.55  # milonga: fewer cadential frills
    elif dance_type == "vals":
        decoration = min(0.85, decoration * 1.1)  # gentle phrase-end turns ok

    enabled = _default_instruments(profile)
    if instruments:
        for k in ("piano", "bandoneon", "strings"):
            if k in instruments:
                enabled[k] = bool(instruments[k])

    for layer, floor in (("bandoneon", 0.5), ("strings", 0.45)):
        if enabled.get(layer) and vols.get(layer, 0) < 0.15:
            vols[layer] = floor

    notes: list[NoteEvent] = []
    chord_events: list[ChordEvent] = []

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

    if enabled.get("piano", True):
        for ch in skeleton["chords"]:
            bar = int(ch["bar"])
            pitches = chord_pitches(tonic, mode, ch["symbol"])
            bar_start = bar * bar_len
            lh = left_hand_for_bar(
                rhythm,
                bar,
                bar_start,
                bar_len,
                pitches,
                articulation,
                beats_per_bar=beats_per_bar,
            )
            for n in lh:
                n.velocity = _apply_vel(n.velocity, vols.get("piano_lh", 0.8))
                notes.append(n)

        rh = _render_melody(
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

    if enabled.get("bandoneon"):
        bn = _bandoneon_pads(
            skeleton,
            spb=spb,
            tonic=tonic,
            mode=mode,
            lyrical=profile.get("personality_type") == "lyrical",
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
        "dance_type": dance_type,
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
