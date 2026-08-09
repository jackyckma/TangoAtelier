from __future__ import annotations

import random
from typing import Any, Literal

from app.engine.catalog import (
    DANCE_TYPES,
    FORMS,
    KEYS,
    KEYS_MAJOR,
    KEYS_MINOR,
    PROGRESSIONS_MAJOR,
    PROGRESSIONS_MINOR,
)
from app.engine.harmony import (
    HARMONIC_MINOR,
    MAJOR_SCALE,
    TONICS,
    chord_pitches,
    relative_key,
)

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


def _alternate_progression(
    rng: random.Random,
    mode: str,
    current_id: str,
) -> tuple[str, list[str]]:
    table = PROGRESSIONS_MINOR if mode == "minor" else PROGRESSIONS_MAJOR
    choices = [k for k in table if k != current_id]
    pid = rng.choice(choices or list(table.keys()))
    return pid, list(table[pid])


def _section_should_modulate(section_name: str) -> bool:
    return section_name in ("B", "A_prime")


def _plan_section_harmony(
    rng: random.Random,
    *,
    section_name: str,
    home_key: str,
    home_mode: str,
    home_tonic: int,
    home_prog_id: str,
    home_progression: list[str],
    user_locked_progression: bool,
) -> dict[str, Any]:
    """Per-section key + progression. Contrast sections often go to relative maj/min."""
    key_name, mode, tonic = home_key, home_mode, home_tonic
    prog_id, progression = home_prog_id, list(home_progression)
    modulation: str | None = None

    if section_name in ("intro", "coda"):
        # Stay home; prefer short cadence feel via same progression
        return {
            "section": section_name,
            "key": key_name,
            "mode": mode,
            "tonic": tonic,
            "progression_id": prog_id,
            "progression": progression,
            "modulation": None,
        }

    if _section_should_modulate(section_name):
        # Relative major/minor is the common Golden Age move
        rel = relative_key(home_key, home_mode, home_tonic)
        if rel is not None and rng.random() < 0.9:
            key_name, mode, tonic = rel
            modulation = "relative_major" if mode == "major" else "relative_minor"
            prog_id, progression = _pick_progression(rng, mode, "random")
        else:
            # Same key, different progression — still breaks the endless loop
            prog_id, progression = _alternate_progression(rng, mode, home_prog_id)
            modulation = "progression_change"

    return {
        "section": section_name,
        "key": key_name,
        "mode": mode,
        "tonic": tonic,
        "progression_id": prog_id,
        "progression": progression,
        "modulation": modulation,
    }


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
    rng: random.Random,
    *,
    bar: int,
    beats_per_bar: int,
    pitches: list[int],
    density: Level,
    variation: Level,
    phrase_end: bool,
    role: str,
    dance_type: str,
) -> list[dict[str, Any]]:
    n = len(pitches)
    if n == 0:
        return []
    active = n
    if density != "high" and phrase_end:
        active = max(1, n - 1)
    if density == "low" and role == "answer":
        active = max(1, min(active, 2))

    notes: list[dict[str, Any]] = []

    if dance_type == "milonga":
        # Snap melody toward habanera / 3+3+2 slots inside the bar
        slots_habanera = [0.0, 0.75, 1.0, 1.5]
        slots_332 = [0.0, 0.75, 1.5]
        slots = slots_332 if variation == "high" else slots_habanera
        picks = slots[:active]
        while len(picks) < active:
            picks.append(min(beats_per_bar - 0.25, picks[-1] + 0.5))
        for j, pitch in enumerate(pitches[:active]):
            start_local = picks[j]
            is_last = j == active - 1
            next_boundary = picks[j + 1] if j + 1 < len(picks) else beats_per_bar
            dur = min(0.55 if not is_last else 0.75, next_boundary - start_local)
            if is_last and phrase_end:
                dur = min(1.0, beats_per_bar - start_local)
            note: dict[str, Any] = {
                "pitch": int(pitch),
                "start_beat": round(bar * beats_per_bar + start_local, 3),
                "duration_beats": round(max(0.2, dur), 3),
                "phrase_role": role,
            }
            if is_last and phrase_end:
                note["phrase_end"] = True
            notes.append(note)
        return notes

    if dance_type == "vals":
        # Land on beat 1; fill 2–3 with lighter motion; longer legato values
        # Prefer 1–3 notes/bar so the waltz pulse stays clear
        active = min(active, 3 if density == "high" else 2 if density == "medium" else 1)
        # Placement: always beat 0, then beat 1 or 2
        placements = [0.0]
        if active >= 2:
            placements.append(1.0 if rng.random() < 0.55 else 2.0)
        if active >= 3:
            placements.append(2.0 if 1.0 in placements else 1.0)
        placements = sorted(placements[:active])
        for j, pitch in enumerate(pitches[:active]):
            start_local = placements[j]
            is_last = j == active - 1
            # Sustain toward next beat / bar end (flowing, not choppy)
            end = placements[j + 1] if j + 1 < len(placements) else beats_per_bar
            dur = (end - start_local) * (1.05 if is_last else 0.95)
            if start_local == 0.0:
                dur = max(dur, 1.2)  # weight the downbeat
            dur = min(dur, beats_per_bar - start_local)
            note = {
                "pitch": int(pitch),
                "start_beat": round(bar * beats_per_bar + start_local, 3),
                "duration_beats": round(max(0.4, dur), 3),
                "phrase_role": role,
            }
            if is_last and phrase_end:
                note["phrase_end"] = True
            notes.append(note)
        return notes

    # tango (default): even-ish placement with optional light syncopation
    step = beats_per_bar / max(active, 1)
    cursor = 0.0
    for j, pitch in enumerate(pitches[:active]):
        offset = 0.0
        if variation == "high" and j > 0 and j % 2 == 1:
            offset = min(step * 0.12, beats_per_bar - cursor - 0.1)
        is_last = j == active - 1
        dur = step * (1.25 if is_last and phrase_end else 0.9)
        dur = min(dur, beats_per_bar - cursor - offset)
        if dur <= 0.05:
            break
        note = {
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
    dance_type: str = "tango",
) -> list[dict[str, Any]]:
    notes_per_half = DENSITY_NOTES[density]
    if dance_type == "milonga" and density != "high":
        notes_per_half = min(4, notes_per_half + 1)  # a bit busier / playful
    if dance_type == "vals":
        notes_per_half = {"low": 1, "medium": 2, "high": 3}[density]

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
                rng,
                bar=bar_q,
                beats_per_bar=beats_per_bar,
                pitches=q_pitches,
                density=density,
                variation=variation,
                phrase_end=phrase_end_q,
                role=role_first,
                dance_type=dance_type,
            )
        )
        last_pitch = q_pitches[-1]
        i += 1

        if not is_pair:
            break

        bar_a = start_bar + i
        symbol_a = chords_for_bars[i]
        a_start = last_pitch
        if var > 0.3 and question_memory:
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
                rng,
                bar=bar_a,
                beats_per_bar=beats_per_bar,
                pitches=a_pitches,
                density=density,
                variation=variation,
                phrase_end=True,
                role="answer",
                dance_type=dance_type,
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
        bias = dance.get("key_bias", "minor")
        if bias == "major":
            pool = KEYS_MAJOR * 3 + KEYS_MINOR  # prefer major for milonga/vals
        elif bias == "minor":
            pool = KEYS_MINOR * 3 + KEYS_MAJOR
        else:
            pool = KEYS
        key_name, mode, tonic = _parse_key(rng.choice(pool))
    else:
        key_name, mode, tonic = _parse_key(key)

    if form_id in (None, "", "random"):
        form_id = rng.choice(list(FORMS.keys()))
    if form_id not in FORMS:
        raise ValueError(f"Unknown form_id: {form_id}")
    form_def = FORMS[form_id]
    sections = form_def["sections"]
    total_bars = sum(b for _, b in sections)

    user_locked_progression = bool(
        progression_id and progression_id not in (None, "", "random")
    )
    home_prog_id, home_progression = _pick_progression(rng, mode, progression_id)
    bars_per_chord = int(dance["bars_per_chord"])

    chords: list[dict[str, Any]] = []
    melody: list[dict[str, Any]] = []
    form_labels: list[str] = []
    harmony_plan: list[dict[str, Any]] = []
    bar = 0

    for section_name, section_bars in sections:
        form_labels.append(section_name)
        sec = _plan_section_harmony(
            rng,
            section_name=section_name,
            home_key=key_name,
            home_mode=mode,
            home_tonic=tonic,
            home_prog_id=home_prog_id,
            home_progression=home_progression,
            user_locked_progression=user_locked_progression,
        )
        harmony_plan.append(sec)

        section_symbols: list[str] = []
        prog = sec["progression"]
        prog_i = 0
        for j in range(section_bars):
            if j % bars_per_chord == 0:
                symbol = prog[prog_i % len(prog)]
                prog_i += 1
            else:
                symbol = section_symbols[-1] if section_symbols else prog[0]
            section_symbols.append(symbol)
            chords.append(
                {
                    "bar": bar,
                    "symbol": symbol,
                    "start_beat": bar * beats_per_bar,
                    "duration_beats": beats_per_bar,
                    "key": sec["key"],
                    "mode": sec["mode"],
                    "tonic": sec["tonic"],
                    "section": section_name,
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
                tonic=int(sec["tonic"]),
                mode=str(sec["mode"]),
                chords_for_bars=section_symbols,
                density=dens,
                variation=melody_variation,
                section_name=section_name,
                dance_type=dance_type,
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
        "default_rhythm": dance.get("default_rhythm"),
        "form_id": form_id,
        "form": form_labels,
        "progression_id": home_prog_id,
        "progression": home_progression,
        "harmony_plan": harmony_plan,
        "melody_density": melody_density,
        "melody_variation": melody_variation,
        "bars": total_bars,
        "chords": chords,
        "melody": melody,
    }
