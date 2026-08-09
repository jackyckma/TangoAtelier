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

# Notes per half-phrase (1 bar of a 2-bar Q or A cell)
DENSITY_NOTES = {"low": 2, "medium": 3, "high": 5}
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


def _nearest(pool: list[int], target: int) -> int:
    return min(pool, key=lambda p: abs(p - target))


def _step_toward(
    rng: random.Random,
    prev: int,
    target: int,
    chord: list[int],
    scale: list[int],
    *,
    must_chord: bool,
) -> int:
    pool = chord if must_chord else (chord + [p for p in scale if abs(p - prev) <= 4])
    # Prefer moving toward target pitch contour
    scored = sorted(pool, key=lambda p: (abs(p - target) * 2 + abs(p - prev), rng.random()))
    return scored[0]


def _phrase_contour(
    rng: random.Random,
    *,
    n: int,
    role: Literal["question", "answer"],
    tonic: int,
    mode: str,
    symbol: str,
    start_pitch: int | None,
    variation: float,
) -> list[int]:
    """Build a short contour that lands on chord tones at start/end; Q rises, A falls."""
    chord = _chord_pool(tonic, mode, symbol)
    scale = _scale_pool(tonic, mode)
    start = start_pitch if start_pitch is not None else rng.choice(chord)
    start = _nearest(chord, start)

    if role == "question":
        # Rise / open: end on 3rd or 5th (or scale tension near chord)
        end_candidates = chord[1:] or chord
        end = rng.choice(end_candidates)
        if end <= start:
            end = _clamp_melody(start + rng.choice([2, 3, 4, 5]))
            end = _nearest(chord + scale, end)
        peak = _clamp_melody(max(start, end) + rng.choice([0, 2, 3]))
    else:
        # Fall / close: end on root (or chord tone)
        end = chord[0]
        if variation > 0.5 and rng.random() < 0.35:
            end = rng.choice(chord)
        peak = start if start >= end else _clamp_melody(start + 2)

    pitches: list[int] = []
    for i in range(n):
        t = i / max(1, n - 1)
        if role == "question":
            # arch: start → peak → slightly open end
            if t < 0.55:
                target = int(start + (peak - start) * (t / 0.55))
            else:
                target = int(peak + (end - peak) * ((t - 0.55) / 0.45))
        else:
            # descend toward resolution
            target = int(start + (end - start) * t)

        must_chord = i == 0 or i == n - 1 or (n >= 4 and i == n // 2)
        prev = pitches[-1] if pitches else start
        pitches.append(
            _step_toward(rng, prev, target, chord, scale, must_chord=must_chord)
        )

    # Enforce chord tone endpoints after contour noise
    pitches[0] = _nearest(chord, pitches[0])
    pitches[-1] = _nearest(chord, pitches[-1] if role == "question" else chord[0])
    if role == "answer":
        pitches[-1] = chord[0] if rng.random() > variation * 0.3 else _nearest(chord, pitches[-1])
    return pitches


def _emit_bar_notes(
    *,
    bar: int,
    beats_per_bar: int,
    pitches: list[int],
    density: Level,
    variation: Level,
    phrase_end: bool,
    role: str,
) -> list[dict[str, Any]]:
    n = len(pitches)
    if n == 0:
        return []
    # Leave air at phrase ends (especially answers)
    active = n
    if density != "high" and phrase_end:
        active = max(1, n - 1)
    if density == "low" and role == "answer":
        active = max(1, min(active, 2))

    step = beats_per_bar / max(active, 1)
    notes: list[dict[str, Any]] = []
    cursor = 0.0
    for j, pitch in enumerate(pitches[:active]):
        offset = 0.0
        if variation == "high" and j > 0 and j % 2 == 1:
            offset = min(step * 0.12, beats_per_bar - cursor - 0.1)
        # Longer values on cadence landing
        is_last = j == active - 1
        dur = step * (1.25 if is_last and phrase_end else 0.9)
        dur = min(dur, beats_per_bar - cursor - offset)
        if dur <= 0.05:
            break
        note: dict[str, Any] = {
            "pitch": int(pitch),
            "start_beat": round(bar * beats_per_bar + cursor + offset, 3),
            "duration_beats": round(dur, 3),
            "phrase_role": role,
        }
        if is_last and phrase_end:
            note["phrase_end"] = True
        notes.append(note)
        cursor += step
    return notes


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
) -> list[dict[str, Any]]:
    notes_per_half = DENSITY_NOTES[density]
    var = VARIATION_STRENGTH[variation]
    notes: list[dict[str, Any]] = []
    last_pitch: int | None = None
    question_memory: list[int] | None = None

    # Process in 2-bar Q/A cells; leftover single bar treated as answer fragment
    i = 0
    while i < bars:
        bar_q = start_bar + i
        symbol_q = chords_for_bars[i]
        is_pair = i + 1 < bars
        role_first: Literal["question", "answer"] = "question" if is_pair else "answer"

        # Reuse / sequence prior question under variation
        if (
            question_memory
            and role_first == "question"
            and section_name in ("A_prime", "A")
            and rng.random() > var
        ):
            q_pitches = [
                _nearest(_chord_pool(tonic, mode, symbol_q), p + rng.choice([0, 0, 2, -2]))
                for p in question_memory
            ]
            q_pitches = q_pitches[:notes_per_half]
            while len(q_pitches) < notes_per_half:
                q_pitches.append(q_pitches[-1])
        else:
            q_pitches = _phrase_contour(
                rng,
                n=notes_per_half,
                role=role_first,
                tonic=tonic,
                mode=mode,
                symbol=symbol_q,
                start_pitch=last_pitch,
                variation=var,
            )

        if role_first == "question":
            question_memory = list(q_pitches)

        phrase_end_q = not is_pair
        notes.extend(
            _emit_bar_notes(
                bar=bar_q,
                beats_per_bar=beats_per_bar,
                pitches=q_pitches,
                density=density,
                variation=variation,
                phrase_end=phrase_end_q,
                role=role_first,
            )
        )
        last_pitch = q_pitches[-1]
        i += 1

        if not is_pair:
            break

        bar_a = start_bar + i
        symbol_a = chords_for_bars[i]
        # Answer starts near question end, resolves into current harmony
        a_start = last_pitch
        if var > 0.3 and question_memory:
            # Sequence answer from inverted/falling transform of question
            mirrored = list(reversed(question_memory))
            a_start = mirrored[0]
        a_pitches = _phrase_contour(
            rng,
            n=notes_per_half,
            role="answer",
            tonic=tonic,
            mode=mode,
            symbol=symbol_a,
            start_pitch=a_start,
            variation=var + (0.1 if section_name == "B" else 0),
        )
        notes.extend(
            _emit_bar_notes(
                bar=bar_a,
                beats_per_bar=beats_per_bar,
                pitches=a_pitches,
                density=density,
                variation=variation,
                phrase_end=True,
                role="answer",
            )
        )
        last_pitch = a_pitches[-1]
        i += 1

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
    melody: list[dict[str, Any]] = []
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
