from __future__ import annotations

import random

from app.engine.harmony import HARMONIC_MINOR, MAJOR_SCALE
from app.engine.types import NoteEvent


def _scale_pitches(tonic: int, mode: str, low: int, high: int) -> list[int]:
    intervals = HARMONIC_MINOR if mode == "minor" else MAJOR_SCALE
    pitches: list[int] = []
    for oct_off in range(-1, 3):
        for iv in intervals:
            p = tonic + iv + oct_off * 12
            if low <= p <= high:
                pitches.append(p)
    return sorted(set(pitches))


def right_hand_for_bar(
    rng: random.Random,
    bar_index: int,
    bar_start: float,
    bar_len: float,
    tonic: int,
    mode: str,
    chord_pitches: list[int],
    articulation: dict,
    ornate: bool,
) -> list[NoteEvent]:
    scale = _scale_pitches(tonic, mode, 60, 84) or [60, 62, 63, 65, 67, 68, 71, 72]
    chord_tones = [p + 12 for p in chord_pitches if p + 12 <= 84]
    if not chord_tones:
        chord_tones = [min(84, max(60, p + 12)) for p in chord_pitches]

    legato = articulation.get("staccato_level", "medium") == "low"
    rubato = articulation.get("rubato_level", "low") == "high"

    notes: list[NoteEvent] = []
    e = bar_len / 4
    density = 3 if ornate else 2
    if articulation.get("pause_frequency") == "high" and bar_index % 4 == 3:
        density = 1

    cursor = e * 0.15 if rubato and bar_index % 2 == 1 else 0.0

    for step in range(density):
        if cursor >= bar_len - e * 0.2:
            break
        if rng.random() < 0.7:
            pitch = rng.choice(chord_tones)
            while pitch < 64:
                pitch += 12
            while pitch > 81:
                pitch -= 12
        else:
            pitch = rng.choice(scale)

        if ornate and step == density - 1:
            notes.append(NoteEvent(pitch, bar_start + cursor, e * 0.45, 78, "piano_rh"))
            nb = pitch + rng.choice([-1, 1, 2])
            notes.append(
                NoteEvent(nb, bar_start + cursor + e * 0.45, e * 0.4, 72, "piano_rh")
            )
            cursor += e * 1.1
        else:
            dur = e * (1.6 if legato else 0.85)
            vel = 76 if legato else 82
            notes.append(NoteEvent(pitch, bar_start + cursor, dur, vel, "piano_rh"))
            cursor += e * (1.2 if legato else 1.0)

    return notes
