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
    "tempo_bpm_range": [62, 62],
    "rhythm_patterns": ["marcato_en_dos"],
    "articulation": {
        "staccato_level": "medium",
        "rubato_level": "low",
        "dynamic_contrast": "medium",
        "pause_frequency": "low",
    },
}


def _bpm(profile: dict, rng: random.Random, skeleton: dict) -> float:
    if profile.get("id") == "simple":
        return float(skeleton.get("default_bpm", 64))
    lo, hi = profile.get("tempo_bpm_range", [60, 66])
    # Keep dance-type character: milonga stays faster
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


def render_skeleton(
    skeleton: dict[str, Any],
    profile: dict,
    *,
    seed: int | None = None,
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

    # For vals (3/4), stretch LH patterns that assume 2/4 by using bar_len correctly
    notes: list[NoteEvent] = []
    chord_events: list[ChordEvent] = []

    for ch in skeleton["chords"]:
        bar = int(ch["bar"])
        symbol = ch["symbol"]
        pitches = chord_pitches(tonic, mode, symbol)
        bar_start = bar * bar_len
        chord_events.append(
            ChordEvent(bar=bar, symbol=symbol, start=bar_start, duration=bar_len)
        )
        notes.extend(
            left_hand_for_bar(
                rhythm, bar, bar_start, bar_len, pitches, articulation
            )
        )

    # RH from skeleton melody — style affects duration/velocity/ornament
    staccato = articulation.get("staccato_level", "medium")
    rubato = articulation.get("rubato_level", "low") == "high"
    for m in skeleton["melody"]:
        start = float(m["start_beat"]) * spb
        dur = float(m["duration_beats"]) * spb
        if staccato == "high":
            dur *= 0.55
        elif staccato == "low":
            dur *= 1.15
        if rubato and int(m["start_beat"]) % 3 == 1:
            start += spb * 0.08
        vel = 76 if staccato == "low" else 86 if staccato == "high" else 80
        # simple style: quieter, cleaner
        if profile.get("id") == "simple":
            vel = 74
            dur = float(m["duration_beats"]) * spb * 0.95
        notes.append(
            NoteEvent(
                pitch=int(m["pitch"]),
                start=start,
                duration=max(0.05, dur),
                velocity=vel,
                track="piano_rh",
            )
        )

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
