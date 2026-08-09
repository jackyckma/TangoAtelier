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
from app.engine.rhythm import choose_rhythm_pair, left_hand_for_bar
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

# Melody-forward mixes: RH must read as the song; LH/backdrop support it.
PERSONALITY_MIX = {
    "neutral": {
        "decoration": 0.15,
        "volumes": {"piano_lh": 0.62, "piano_rh": 1.0, "bandoneon": 0.0, "strings": 0.0},
    },
    "rhythmic": {
        "decoration": 0.35,
        "volumes": {"piano_lh": 0.78, "piano_rh": 1.0, "bandoneon": 0.4, "strings": 0.2},
    },
    "lyrical": {
        "decoration": 0.55,
        "volumes": {"piano_lh": 0.48, "piano_rh": 1.0, "bandoneon": 0.55, "strings": 0.45},
    },
    "smooth_powerful": {
        "decoration": 0.3,
        "volumes": {"piano_lh": 0.7, "piano_rh": 0.98, "bandoneon": 0.4, "strings": 0.5},
    },
    "dramatic": {
        "decoration": 0.65,
        "volumes": {"piano_lh": 0.72, "piano_rh": 1.0, "bandoneon": 0.5, "strings": 0.55},
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


def _rhythm_pair_for_dance(
    profile: dict, dance_type: str, rng: random.Random
) -> tuple[str, str | None]:
    """Primary groove + optional secondary colour (not whole-piece replace)."""
    dance = DANCE_TYPES.get(dance_type, DANCE_TYPES["tango"])
    if dance_type == "vals":
        return "vals_bass_chord", None
    if dance_type == "milonga":
        primary = str(dance.get("default_rhythm") or "milonga_habanera")
        secondary = str(dance.get("alt_rhythm") or "milonga_332")
        if profile.get("id") == "simple":
            return primary, None
        return primary, secondary
    if profile.get("id") == "simple":
        return str(dance.get("default_rhythm") or "marcato_en_dos"), None
    return choose_rhythm_pair(profile)


def _pattern_for_bar(
    primary: str,
    secondary: str | None,
    bar: int,
    *,
    extras: list[str] | None = None,
) -> str:
    """Rotate groove colour without abandoning the home pulse.

    Layout in 8-bar windows: home → home → colour → home → home → home → colour2 → home
    so the ear gets variety but still locks to the primary marcato/habanera feel.
    """
    colour = [p for p in ((secondary,) if secondary else ()) + tuple(extras or ()) if p and p != primary]
    if not colour:
        return primary
    slot = bar % 8
    if slot in (2, 6):
        return colour[(bar // 8 + (0 if slot == 2 else 1)) % len(colour)]
    return primary


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
        voice = m.get("voice") or "lead"
        drama = m.get("drama") or "normal"
        energy = float(m.get("energy") or 0.5)
        # Keep lead cantabile; only chop fill notes when staccato is high
        if voice != "lead" and staccato == "high":
            dur *= 0.65
        elif staccato == "low" or voice == "lead":
            dur *= 1.08 if voice == "lead" else 1.0
        if drama == "dense":
            dur *= 0.75
        if voice == "lead":
            vel = 96 if staccato != "low" else 88
        elif voice == "fill":
            vel = 64
        else:
            vel = 78
        # Energy arc → velocity (climax punches harder)
        vel = int(vel * (0.75 + 0.45 * energy))
        if drama == "climax":
            vel = min(127, vel + 12)
            # Octave reinforcement for a short dramatic peak
            notes.append(
                NoteEvent(pitch - 12, start, max(0.05, dur * 0.9), max(50, vel - 25), "piano_rh")
            )
        notes.append(NoteEvent(pitch, start, max(0.05, dur), min(127, vel), "piano_rh"))

        orn_p = decoration
        if drama == "climax":
            orn_p = min(1.0, decoration + 0.35)
        elif drama == "dense":
            orn_p *= 0.4
        if (
            voice == "lead"
            and m.get("phrase_end")
            and m.get("phrase_role") in ("answer", "cadence")
            and rng.random() < orn_p
        ):
            notes.extend(_phrase_end_ornament(rng, pitch, start, dur, spb, vel))
    return notes


def _chord_tonality(ch: dict, skeleton: dict) -> tuple[int, str]:
    return int(ch.get("tonic", skeleton["tonic"])), str(ch.get("mode", skeleton["mode"]))


def _bandoneon_pads(
    skeleton: dict,
    *,
    spb: float,
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
        tonic, mode = _chord_tonality(ch, skeleton)
        hold_bars = 1
        while (
            i + hold_bars < len(chords)
            and chords[i + hold_bars]["symbol"] == symbol
            and chords[i + hold_bars].get("key", ch.get("key")) == ch.get("key")
            and hold_bars < 2
        ):
            hold_bars += 1
        pitches = chord_pitches(tonic, mode, symbol, octave_shift=0)
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
    dramatic: bool,
) -> list[NoteEvent]:
    notes: list[NoteEvent] = []
    beats_per_bar = int(skeleton["beats_per_bar"])
    bar_len = beats_per_bar * spb
    for ch in skeleton["chords"]:
        bar = int(ch["bar"])
        if not dramatic and bar % 2 == 1:
            continue
        tonic, mode = _chord_tonality(ch, skeleton)
        pitches = chord_pitches(tonic, mode, ch["symbol"], octave_shift=1)
        start = bar * bar_len
        dur = bar_len * (1.85 if dramatic and bar % 4 == 0 else 1.6)
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
    rhythm_primary, rhythm_secondary = _rhythm_pair_for_dance(profile, dance_type, rng)
    rhythm_extras = [
        p
        for p in (profile.get("rhythm_patterns") or [])
        if p not in (rhythm_primary, rhythm_secondary)
    ]
    # Single-pattern styles (e.g. D'Arienzo) still need occasional colour
    if dance_type == "tango" and not rhythm_secondary and not rhythm_extras and profile.get("id") != "simple":
        rhythm_extras = ["sincopa"] if rhythm_primary.startswith("marcato") else ["marcato_en_dos"]
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
            section = str(ch.get("section") or "A")
            ch_tonic, ch_mode = _chord_tonality(ch, skeleton)
            pitches = chord_pitches(ch_tonic, ch_mode, ch["symbol"])
            bar_start = bar * bar_len
            # Intro/bridge/coda: keep groove, but lighter so form edges read clearly
            pattern = _pattern_for_bar(
                rhythm_primary, rhythm_secondary, bar, extras=rhythm_extras
            )
            if section in ("intro", "bridge"):
                # Intro: stay on home groove but LH pitch cells still rotate by bar
                pattern = rhythm_primary
            lh = left_hand_for_bar(
                pattern,
                bar,
                bar_start,
                bar_len,
                pitches,
                articulation,
                beats_per_bar=beats_per_bar,
            )
            lh_scale = vols.get("piano_lh", 0.8)
            drama_tag = str(ch.get("drama") or "normal")
            energy = float(ch.get("energy") or 0.5)
            if section in ("intro", "bridge"):
                lh_scale *= 0.85
            elif section in ("A", "A_prime"):
                lh_scale *= 0.82  # make room for the theme
            if drama_tag == "pause":
                # Tango hole: keep a single bass hit or full silence
                lh = lh[:1] if lh and rng.random() < 0.55 else []
                lh_scale *= 0.55
            elif drama_tag == "climax":
                lh_scale *= 1.15
            elif drama_tag == "dense":
                lh_scale *= 1.05
            else:
                lh_scale *= 0.85 + 0.3 * energy
            for n in lh:
                # Drop some weak-beat LH under lead so melody isn't carpeted
                if section in ("A", "A_prime", "B") and beats_per_bar == 2:
                    rel = (n.start - bar_start) / max(bar_len, 1e-6)
                    if 0.4 < rel < 0.6 and n.velocity < 90 and drama_tag != "climax":
                        continue
                n.velocity = _apply_vel(n.velocity, lh_scale)
                notes.append(n)

        rh = _render_melody(
            rng,
            skeleton["melody"],
            decoration=decoration,
            spb=spb,
            staccato=str(articulation.get("staccato_level", "medium")),
        )
        for n in rh:
            n.velocity = _apply_vel(n.velocity, vols.get("piano_rh", 1.0))
            notes.append(n)

    if enabled.get("bandoneon"):
        bn = _bandoneon_pads(
            skeleton,
            spb=spb,
            lyrical=profile.get("personality_type") == "lyrical",
        )
        for n in bn:
            # Mute pads during intro — leave air for the theme entrance
            bar_idx = int(n.start / max(bar_len, 1e-6))
            sec = "A"
            if bar_idx < len(skeleton["chords"]):
                sec = str(skeleton["chords"][bar_idx].get("section") or "A")
            if sec == "intro":
                continue
            scale = vols.get("bandoneon", 0.7) * (0.65 if sec in ("A", "A_prime") else 1.0)
            n.velocity = _apply_vel(n.velocity, scale)
            notes.append(n)

    if enabled.get("strings"):
        st = _strings_pads(
            skeleton,
            spb=spb,
            dramatic=profile.get("personality_type") == "dramatic",
        )
        for n in st:
            n.velocity = _apply_vel(n.velocity, vols.get("strings", 0.6))
            notes.append(n)

    notes.sort(key=lambda n: (n.start, n.track, n.pitch))
    rhythm_label = rhythm_primary
    if rhythm_secondary:
        rhythm_label = f"{rhythm_primary}+{rhythm_secondary}"
    draft = PieceDraft(
        orchestra_id=profile["id"],
        seed=seed,
        bpm=bpm,
        key_name=skeleton["key"],
        mode=mode,
        time_signature=time_signature,  # type: ignore[arg-type]
        rhythm_pattern=rhythm_label,
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
                "key": skeleton["chords"][i].get("key"),
                "mode": skeleton["chords"][i].get("mode"),
                "section": skeleton["chords"][i].get("section"),
            }
            for i, c in enumerate(draft.chords)
        ],
        "harmony_plan": skeleton.get("harmony_plan"),
        "drama": skeleton.get("drama"),
        "notes": notes_payload(draft.notes),
    }
    if include_midi:
        payload["midi_base64"] = score_to_midi_base64(score)
    if include_musicxml:
        payload["musicxml"] = score_to_musicxml(score)
    return payload
