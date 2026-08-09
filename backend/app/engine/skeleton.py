from __future__ import annotations

import random
from typing import Any, Literal

from app.engine.catalog import (
    DANCE_TYPES,
    FORMS,
    KEYS,
    PROGRESSIONS_MAJOR,
    PROGRESSIONS_MINOR,
)
from app.engine.harmony import HARMONIC_MINOR, MAJOR_SCALE, TONICS, chord_pitches

Level = Literal["low", "medium", "high"]

DENSITY_NOTES = {"low": 2, "medium": 4, "high": 6}
VARIATION_STRENGTH = {"low": 0.15, "medium": 0.4, "high": 0.7}


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


def _clamp_melody(p: int) -> int:
    while p < 62:
        p += 12
    while p > 81:
        p -= 12
    return p


def _scale_pool(tonic: int, mode: str) -> list[int]:
    intervals = HARMONIC_MINOR if mode == "minor" else MAJOR_SCALE
    return [_clamp_melody(tonic + iv + oct * 12) for oct in (0, 1) for iv in intervals]


def _chord_pool(tonic: int, mode: str, symbol: str) -> list[int]:
    return [_clamp_melody(p + 12) for p in chord_pitches(tonic, mode, symbol)]


def _build_motif(
    rng: random.Random,
    tonic: int,
    mode: str,
    symbol: str,
    length: int,
) -> list[int]:
    chord = _chord_pool(tonic, mode, symbol)
    scale = _scale_pool(tonic, mode)
    motif = [rng.choice(chord)]
    for _ in range(length - 1):
        prev = motif[-1]
        candidates = [p for p in (chord + scale) if abs(p - prev) <= 7]
        if not candidates:
            candidates = chord
        # Prefer stepwise
        step = [p for p in candidates if abs(p - prev) <= 3]
        motif.append(rng.choice(step or candidates))
    return motif


def _vary_motif(
    rng: random.Random,
    motif: list[int],
    strength: float,
    tonic: int,
    mode: str,
    symbol: str,
) -> list[int]:
    if strength <= 0:
        return list(motif)
    scale = _scale_pool(tonic, mode)
    chord = _chord_pool(tonic, mode, symbol)
    out = []
    for p in motif:
        if rng.random() < strength:
            options = [x for x in chord + scale if abs(x - p) <= 5]
            out.append(rng.choice(options) if options else p)
        else:
            out.append(p)
    # occasional sequence transposition
    if rng.random() < strength * 0.5:
        shift = rng.choice([-2, -1, 1, 2])
        out = [_clamp_melody(p + shift) for p in out]
    return out


def _melody_for_section(
    rng: random.Random,
    *,
    start_bar: int,
    bars: int,
    beats_per_bar: int,
    tonic: int,
    mode: str,
    chords_for_bars: list[str],
    density: Level,
    variation: Level,
    section_name: str,
) -> list[dict[str, float | int]]:
    notes_per_bar = DENSITY_NOTES[density]
    var = VARIATION_STRENGTH[variation]
    # Motif length ~ half bar to full bar of notes
    motif_len = max(2, notes_per_bar // 2)
    first_symbol = chords_for_bars[0]
    motif = _build_motif(rng, tonic, mode, first_symbol, motif_len)

    notes: list[dict[str, float | int]] = []
    for i in range(bars):
        bar = start_bar + i
        symbol = chords_for_bars[i]
        use_motif = list(motif)
        if section_name in ("A_prime", "B") or i > 0:
            use_motif = _vary_motif(rng, motif, var + (0.15 if section_name == "B" else 0), tonic, mode, symbol)

        # Expand / shrink motif to notes_per_bar
        pitches: list[int] = []
        while len(pitches) < notes_per_bar:
            pitches.extend(use_motif)
        pitches = pitches[:notes_per_bar]

        # Phrase arc: slight rise mid-phrase
        if notes_per_bar >= 4:
            mid = notes_per_bar // 2
            pitches[mid] = _clamp_melody(pitches[mid] + rng.choice([0, 2, 3]))

        step = beats_per_bar / notes_per_bar
        # Leave a breath at end of every 2 bars when density not high
        active = notes_per_bar if density == "high" or i % 2 == 0 else max(2, notes_per_bar - 1)
        cursor = 0.0
        for j, pitch in enumerate(pitches[:active]):
            # syncopation hint for high variation
            offset = step * 0.15 if variation == "high" and j % 2 == 1 else 0.0
            dur = step * (0.85 if density == "high" else 1.05)
            dur = min(dur, beats_per_bar - cursor - offset)
            if dur <= 0.05:
                break
            notes.append(
                {
                    "pitch": int(pitch),
                    "start_beat": round(bar * beats_per_bar + cursor + offset, 3),
                    "duration_beats": round(dur, 3),
                }
            )
            cursor += step
        # Update motif memory occasionally
        if rng.random() < var:
            motif = pitches[:motif_len]
    return notes


def build_skeleton(
    *,
    dance_type: str = "tango",
    key: str | None = None,
    progression_id: str | None = "random",
    form_id: str | None = "intro_aa_coda",
    melody_density: Level = "medium",
    melody_variation: Level = "medium",
    seed: int | None = None,
) -> dict[str, Any]:
    seed = int(seed if seed is not None else random.randint(1, 2_147_483_647))
    rng = random.Random(seed)

    if melody_density not in DENSITY_NOTES:
        raise ValueError("melody_density must be low|medium|high")
    if melody_variation not in VARIATION_STRENGTH:
        raise ValueError("melody_variation must be low|medium|high")

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
    chord_symbols_by_bar: list[str] = []

    for section_name, section_bars in sections:
        form_labels.append(section_name)
        section_symbols: list[str] = []
        for _ in range(section_bars):
            if bar % bars_per_chord == 0:
                symbol = progression[prog_i % len(progression)]
                prog_i += 1
            else:
                symbol = chord_symbols_by_bar[-1] if chord_symbols_by_bar else progression[0]
            chord_symbols_by_bar.append(symbol)
            section_symbols.append(symbol)
            chords.append(
                {
                    "bar": bar,
                    "symbol": symbol,
                    "start_beat": bar * beats_per_bar,
                    "duration_beats": beats_per_bar,
                }
            )
            bar += 1

        # Intro/coda: slightly sparser melody
        dens: Level = melody_density
        if section_name in ("intro", "coda") and melody_density == "high":
            dens = "medium"
        elif section_name in ("intro", "coda") and melody_density == "medium":
            dens = "low"

        melody.extend(
            _melody_for_section(
                rng,
                start_bar=bar - section_bars,
                bars=section_bars,
                beats_per_bar=beats_per_bar,
                tonic=tonic,
                mode=mode,
                chords_for_bars=section_symbols,
                density=dens,
                variation=melody_variation,
                section_name=section_name,
            )
        )

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
        "melody_density": melody_density,
        "melody_variation": melody_variation,
        "bars": total_bars,
        "chords": chords,
        "melody": melody,
    }
