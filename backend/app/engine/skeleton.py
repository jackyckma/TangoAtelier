from __future__ import annotations

import random
from typing import Any

from app.engine.catalog import (
    DANCE_TYPES,
    FORMS,
    KEYS,
    PROGRESSIONS_MAJOR,
    PROGRESSIONS_MINOR,
)
from app.engine.harmony import HARMONIC_MINOR, MAJOR_SCALE, TONICS, chord_pitches


def _parse_key(key_name: str) -> tuple[str, str, int]:
    parts = key_name.strip().split()
    tonic_letter = parts[0]
    mode = "minor" if len(parts) > 1 and parts[1].startswith("min") else "major"
    tonic = TONICS.get(tonic_letter, 57)
    return key_name if " " in key_name else f"{tonic_letter} {mode}", mode, tonic


def _pick_progression(rng: random.Random, mode: str, progression_id: str | None) -> tuple[str, list[str]]:
    table = PROGRESSIONS_MINOR if mode == "minor" else PROGRESSIONS_MAJOR
    if progression_id and progression_id != "random" and progression_id in table:
        return progression_id, list(table[progression_id])
    pid = rng.choice(list(table.keys()))
    return pid, list(table[pid])


def _melody_for_bar(
    rng: random.Random,
    bar: int,
    beats_per_bar: int,
    tonic: int,
    mode: str,
    symbol: str,
    ornate: bool,
) -> list[dict[str, float | int]]:
    """Neutral melody skeleton in beat units (not seconds)."""
    scale = HARMONIC_MINOR if mode == "minor" else MAJOR_SCALE
    chord = chord_pitches(tonic, mode, symbol)
    chord_tones = []
    for p in chord:
        while p < 64:
            p += 12
        while p > 79:
            p -= 12
        chord_tones.append(p)
    scale_pitches = [tonic + iv + 12 for iv in scale if 60 <= tonic + iv + 12 <= 81]

    notes: list[dict[str, float | int]] = []
    density = 3 if ornate else 2
    cursor = 0.0
    step = beats_per_bar / density
    for i in range(density):
        pitch = rng.choice(chord_tones if rng.random() < 0.75 else scale_pitches or chord_tones)
        dur = min(step * 0.9, beats_per_bar - cursor)
        if dur <= 0.05:
            break
        notes.append(
            {
                "pitch": int(pitch),
                "start_beat": round(bar * beats_per_bar + cursor, 3),
                "duration_beats": round(dur, 3),
            }
        )
        cursor += step
    return notes


def build_skeleton(
    *,
    dance_type: str = "tango",
    key: str | None = None,
    progression_id: str | None = "random",
    form_id: str | None = "intro_aa_coda",
    seed: int | None = None,
) -> dict[str, Any]:
    seed = int(seed if seed is not None else random.randint(1, 2_147_483_647))
    rng = random.Random(seed)

    if dance_type not in DANCE_TYPES:
        raise ValueError(f"Unknown dance_type: {dance_type}")
    dance = DANCE_TYPES[dance_type]
    beats_per_bar = dance["time_signature"][0]

    if key in (None, "", "random"):
        key_name, mode, tonic = _parse_key(rng.choice(KEYS))
    else:
        key_name, mode, tonic = _parse_key(key)

    if form_id in (None, "", "random"):
        form_id = rng.choice(list(FORMS.keys()))
    if form_id not in FORMS:
        raise ValueError(f"Unknown form_id: {form_id}")
    form_def = FORMS[form_id]
    sections = form_def["sections"]
    total_bars = sum(b for _, b in sections)

    prog_id, progression = _pick_progression(rng, mode, progression_id)
    bars_per_chord = int(dance["bars_per_chord"])

    chords: list[dict[str, Any]] = []
    melody: list[dict[str, float | int]] = []
    form_labels: list[str] = []
    bar = 0
    prog_i = 0
    for section_name, section_bars in sections:
        form_labels.append(section_name)
        ornate = section_name in ("A_prime", "B")
        for _ in range(section_bars):
            if bar % bars_per_chord == 0:
                symbol = progression[prog_i % len(progression)]
                prog_i += 1
            else:
                symbol = chords[-1]["symbol"] if chords else progression[0]
            chords.append(
                {
                    "bar": bar,
                    "symbol": symbol,
                    "start_beat": bar * beats_per_bar,
                    "duration_beats": beats_per_bar,
                }
            )
            melody.extend(
                _melody_for_bar(
                    rng, bar, beats_per_bar, tonic, mode, symbol, ornate=ornate
                )
            )
            bar += 1

    return {
        "seed": seed,
        "dance_type": dance_type,
        "key": key_name,
        "mode": mode,
        "tonic": tonic,
        "time_signature": list(dance["time_signature"]),
        "beats_per_bar": beats_per_bar,
        "default_bpm": dance["default_bpm"],
        "form_id": form_id,
        "form": form_labels,
        "progression_id": prog_id,
        "progression": progression,
        "bars": total_bars,
        "chords": chords,
        "melody": melody,
    }
