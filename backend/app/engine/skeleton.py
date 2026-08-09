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

# Target lead attacks per bar (informed by real tango MIDI textures:
# accompaniment is often 8th/16th-dense; piano RH mixes cantabile with 16ths).
# Previously we hard-capped tango lead at 2 notes/bar — density controls did nothing.
DENSITY_NOTES_PER_BAR = {
    "tango": {"low": 3, "medium": 6, "high": 10},
    "milonga": {"low": 4, "medium": 7, "high": 12},
    "vals": {"low": 3, "medium": 5, "high": 8},
}
# Stronger spread so medium/high actually change contours & reuse behaviour
VARIATION_STRENGTH = {"low": 0.25, "medium": 0.55, "high": 0.85}


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

    if section_name == "bridge":
        # Dominant pivot — short cycle; rendered 1 bar/chord so it actually audibly moves
        if home_mode == "minor":
            progression = ["V7", "V7", "i", "V7"]
            prog_id = "bridge_dominant_minor"
        else:
            progression = ["V7", "V7", "I", "V7"]
            prog_id = "bridge_dominant_major"
        return {
            "section": section_name,
            "key": key_name,
            "mode": mode,
            "tonic": tonic,
            "progression_id": prog_id,
            "progression": progression,
            "modulation": "bridge_dominant",
            "bars_per_chord": 1,
        }

    if section_name in ("intro", "coda"):
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
        rel = relative_key(home_key, home_mode, home_tonic)
        if rel is not None and rng.random() < 0.9:
            key_name, mode, tonic = rel
            modulation = "relative_major" if mode == "major" else "relative_minor"
            prog_id, progression = _pick_progression(rng, mode, "random")
        else:
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


# Real tango piano RH often spans ~2–3 octaves; we previously locked ~67–84 (~1 octave).
MELODY_LO = 55  # G3
MELODY_HI = 96  # C7


def _clamp_melody(p: int) -> int:
    """Lead register — wide enough for phrase peaks without leaving the piano tessitura."""
    while p < MELODY_LO:
        p += 12
    while p > MELODY_HI:
        p -= 12
    return p


def _scale_pool(tonic: int, mode: str) -> list[int]:
    intervals = HARMONIC_MINOR if mode == "minor" else MAJOR_SCALE
    return [
        _clamp_melody(tonic + iv + oct * 12)
        for oct in (-1, 0, 1, 2)
        for iv in intervals
    ]


def _chord_pool(tonic: int, mode: str, symbol: str) -> list[int]:
    # Chord tones across the melody register (not a single cramped octave)
    return [
        _clamp_melody(p + oct)
        for p in chord_pitches(tonic, mode, symbol)
        for oct in (0, 12, 24)
    ]


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
    allow_unison: bool = False,
) -> int:
    """Prefer scale steps toward the contour target — tango phrases walk more than they jump."""
    near_scale = [p for p in scale if abs(p - prev) <= 2]
    near_chord = [p for p in chord if abs(p - prev) <= 4]
    if must_chord:
        pool = near_chord or chord
    else:
        pool = near_scale or near_chord or (chord + scale)
    if not allow_unison:
        moved = [p for p in pool if p != prev]
        if moved:
            pool = moved
    # Soft cap: rarely jump more than a fourth from prev
    tight = [p for p in pool if abs(p - prev) <= 5]
    if tight:
        pool = tight
    scored = sorted(
        pool,
        key=lambda p: (
            abs(p - target),
            abs(p - prev),
            0 if p in chord else 1,
            rng.random(),
        ),
    )
    return scored[0]


def _phrase_register_bias(
    rng: random.Random,
    *,
    section_name: str,
    role: Literal["question", "answer"],
    drama_high: bool,
    variation: float,
) -> int:
    """Skeleton-level register plan: songs move between mid and high phrases."""
    if drama_high:
        return 12
    if section_name in ("B", "A_prime") and role == "question":
        return 12 if rng.random() < 0.7 else 0
    if section_name == "A" and role == "question" and rng.random() < 0.25 + variation * 0.2:
        return 12
    if role == "answer" and rng.random() < 0.2:
        return -12
    return 0


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
    register_bias: int = 0,
) -> list[int]:
    """Short motivic contour: mostly steps, chord tones on edges, one directed shape."""
    chord = _chord_pool(tonic, mode, symbol)
    scale = _scale_pool(tonic, mode)
    # Prefer chord tones near the intended register band
    band_lo = 60 + register_bias
    band_hi = 79 + register_bias
    band_chord = [p for p in chord if band_lo <= p <= band_hi] or chord
    start = start_pitch if start_pitch is not None else rng.choice(band_chord)
    if register_bias:
        start = _nearest(band_chord, start + register_bias)
    else:
        start = _nearest(band_chord, start)
    # "leap" shapes made phrases sound random — keep directed arches/rises/falls
    shape = rng.choice(["arch", "rise", "fall", "wave"])

    if role == "question":
        end_candidates = band_chord[1:] or band_chord
        end = rng.choice(end_candidates)
        if abs(end - start) < 2:
            end = _nearest(band_chord + scale, _clamp_melody(start + rng.choice([2, 3, 4])))
        peak = _clamp_melody(max(start, end) + rng.choice([3, 4, 5, 7]))
    else:
        end = _nearest(band_chord, chord[0] + (register_bias if register_bias > 0 else 0))
        if variation > 0.55 and rng.random() < 0.35:
            end = rng.choice(band_chord)
        peak = _clamp_melody(max(start, end) + rng.choice([2, 3, 5]))

    pitches: list[int] = []
    for i in range(n):
        t = i / max(1, n - 1)
        if shape == "rise":
            target = int(start + (end - start) * t)
        elif shape == "fall":
            hi = max(start, peak)
            target = int(hi + (end - hi) * t)
        elif shape == "wave":
            # Up then slight dip — common sung tango gesture without wild leaps
            mid = _clamp_melody((start + end) // 2 + 2)
            if t < 0.5:
                target = int(start + (mid - start) * (t / 0.5))
            else:
                target = int(mid + (end - mid) * ((t - 0.5) / 0.5))
        else:
            if t < 0.55:
                target = int(start + (peak - start) * (t / 0.55))
            else:
                target = int(peak + (end - peak) * ((t - 0.55) / 0.45))

        must_chord = i == 0 or i == n - 1
        prev = pitches[-1] if pitches else start
        pitches.append(
            _step_toward(
                rng,
                prev,
                target,
                chord,
                scale,
                must_chord=must_chord,
                allow_unison=False,
            )
        )

    pitches[0] = _nearest(chord, pitches[0])
    if role == "answer":
        pitches[-1] = chord[0] if rng.random() > variation * 0.35 else _nearest(chord, pitches[-1])
    else:
        pitches[-1] = _nearest(chord, pitches[-1])
    # Break static cells
    for i in range(1, len(pitches)):
        if pitches[i] == pitches[i - 1]:
            alt = [p for p in scale if 0 < abs(p - pitches[i - 1]) <= 2]
            if alt:
                pitches[i] = rng.choice(alt)
    return pitches


def _build_drama_map(
    rng: random.Random,
    sections: list[tuple[str, int]],
    *,
    dance_type: str,
    variation: Level,
) -> dict[str, Any]:
    """Per-bar tension plan: pauses (silence), dense bursts, climax."""
    bar_sections: list[str] = []
    for name, n in sections:
        bar_sections.extend([name] * n)
    total = len(bar_sections)
    var = VARIATION_STRENGTH[variation]

    # Climax: late A_prime, else late final A before coda
    climax_candidates = [i for i, s in enumerate(bar_sections) if s == "A_prime"]
    if not climax_candidates:
        climax_candidates = [i for i, s in enumerate(bar_sections) if s in ("A", "B")]
    climax_bar = (
        climax_candidates[int(len(climax_candidates) * 0.7)]
        if climax_candidates
        else max(0, total - 5)
    )
    # Stretch climax across 2–3 bars
    climax_bars = {climax_bar, min(total - 1, climax_bar + 1)}
    if var > 0.5:
        climax_bars.add(min(total - 1, climax_bar + 2))

    pause_bars: set[int] = set()
    # Phrase-end holes (classic tango air) — more in tango than milonga
    pause_budget = (3 if dance_type == "tango" else 1) + int(var * 3)
    pause_pool = [
        i
        for i, s in enumerate(bar_sections)
        if s in ("A", "A_prime", "B") and i % 4 == 3 and i not in climax_bars
    ]
    rng.shuffle(pause_pool)
    for i in pause_pool[:pause_budget]:
        pause_bars.add(i)
    # Breath into coda
    for i, s in enumerate(bar_sections):
        if s == "coda" and i > 0 and bar_sections[i - 1] != "coda":
            pause_bars.add(i - 1)

    dense_bars: set[int] = set()
    dense_budget = (1 if dance_type == "vals" else 2) + int(var * 3)
    dense_pool = [
        i
        for i, s in enumerate(bar_sections)
        if s in ("A", "A_prime", "B") and i not in pause_bars
    ]
    # Prefer just before climax
    dense_pool.sort(key=lambda i: abs(i - climax_bar))
    for i in dense_pool[:dense_budget]:
        dense_bars.add(i)

    energy: dict[int, float] = {}
    for i, s in enumerate(bar_sections):
        if s == "intro":
            e = 0.25
        elif s == "bridge":
            e = 0.55 + 0.1 * var
        elif s == "coda":
            e = 0.35
        elif s == "B":
            e = 0.65
        elif s == "A_prime":
            e = 0.7
        else:
            e = 0.45 + 0.2 * (i / max(1, total - 1))
        if i in dense_bars:
            e = min(1.0, e + 0.15)
        if i in climax_bars:
            e = 1.0
        if i in pause_bars:
            e = max(0.1, e - 0.35)
        energy[i] = round(e, 3)

    return {
        "climax_bars": sorted(climax_bars),
        "pause_bars": sorted(pause_bars),
        "dense_bars": sorted(dense_bars),
        "energy": energy,
    }


def _tag_voice(notes: list[dict[str, Any]], voice: str) -> list[dict[str, Any]]:
    for n in notes:
        n["voice"] = voice
    return notes


def _sixteenth_slots(beats_per_bar: int) -> list[float]:
    """Beat offsets on a 16th-note grid inside one bar."""
    step = 0.25  # one sixteenth in quarter-note beats
    n = int(round(beats_per_bar / step))
    return [round(i * step, 3) for i in range(n)]


def _pick_grid_placements(
    rng: random.Random,
    *,
    beats_per_bar: int,
    count: int,
    density: Level,
    dance_type: str,
) -> list[float]:
    """Prefer strong beats, then &s, then 16ths — denser levels unlock finer slots."""
    slots = _sixteenth_slots(beats_per_bar)
    if count <= 0:
        return []
    # Priority tiers (indices into 16th grid)
    strong = [i for i, s in enumerate(slots) if abs(s - round(s)) < 1e-9]  # on-beat
    eighths = [i for i, s in enumerate(slots) if abs((s * 2) - round(s * 2)) < 1e-9 and i not in strong]
    sixteenths = [i for i in range(len(slots)) if i not in strong and i not in eighths]

    ordered: list[int] = []
    if density == "low":
        pool = strong + eighths[: max(1, len(eighths) // 2)]
    elif density == "medium":
        pool = strong + eighths + sixteenths[::2]
    else:
        pool = strong + eighths + sixteenths

    # Always include beat 1
    if 0 in pool and 0 not in ordered:
        ordered.append(0)
    rng.shuffle(pool)
    for i in pool:
        if i not in ordered:
            ordered.append(i)
        if len(ordered) >= count:
            break
    # If still short, take remaining grid in order
    for i in range(len(slots)):
        if len(ordered) >= count:
            break
        if i not in ordered:
            ordered.append(i)
    placements = sorted(slots[i] for i in ordered[:count])

    # Milonga: bias toward habanera / 3+3+2 accents when sparse enough to matter
    if dance_type == "milonga" and density != "high" and count <= 4:
        accent = [0.0, 0.75, 1.0, 1.5][:count]
        return [min(a, beats_per_bar - 0.05) for a in accent]
    return placements


def _expand_pitches_to_count(
    rng: random.Random,
    pitches: list[int],
    count: int,
    tonic: int,
    mode: str,
    symbol: str,
) -> list[int]:
    """Interpolate a short contour onto `count` scale steps (directed, few unisons/leaps)."""
    if count <= 0:
        return []
    chord = _chord_pool(tonic, mode, symbol)
    scale = sorted(set(_scale_pool(tonic, mode) + chord))
    if not pitches:
        pitches = [rng.choice(chord)]
    # Anchor skeleton pitches across the bar, then walk between them
    anchors = list(pitches)
    while len(anchors) < 2:
        anchors.append(_nearest(chord, anchors[-1] + rng.choice([2, -2, 3])))
    anchors = anchors[: max(2, min(len(anchors), 4))]
    anchors[0] = _nearest(chord, anchors[0])
    anchors[-1] = _nearest(chord, anchors[-1])

    out: list[int] = []
    for i in range(count):
        t = i / max(1, count - 1)
        # Which anchor segment?
        seg = t * (len(anchors) - 1)
        a_i = int(seg)
        a_i = min(a_i, len(anchors) - 2)
        local_t = seg - a_i
        target = int(anchors[a_i] + (anchors[a_i + 1] - anchors[a_i]) * local_t)
        prev = out[-1] if out else anchors[0]
        # Walk at most a step (or small skip) toward target
        candidates = [p for p in scale if 0 < abs(p - prev) <= 2]
        if not candidates:
            candidates = [p for p in scale if 0 < abs(p - prev) <= 4] or [target]
        # Prefer continuing in the contour direction
        direction = 1 if target >= prev else -1
        directed = [p for p in candidates if (p - prev) * direction >= 0]
        pool = directed or candidates
        choice = min(pool, key=lambda p: (abs(p - target), abs(p - prev), rng.random()))
        # Rare neighbor tone for figuration colour (not a random leap)
        if i > 0 and i < count - 1 and rng.random() < 0.12:
            nbr = [p for p in scale if abs(p - choice) == 1]
            if nbr:
                choice = rng.choice(nbr)
        out.append(choice)

    out[0] = _nearest(chord, out[0])
    out[-1] = _nearest(chord, out[-1])
    # Kill remaining unisons by nudging to neighbor scale degree
    for i in range(1, len(out)):
        if out[i] == out[i - 1]:
            nbr = [p for p in scale if 0 < abs(p - out[i - 1]) <= 2]
            if nbr:
                out[i] = min(nbr, key=lambda p: abs(p - (out[i + 1] if i + 1 < len(out) else out[i - 1])))
    return out[:count]


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
    voice: str = "lead",
    tonic: int | None = None,
    mode: str | None = None,
    symbol: str | None = None,
) -> list[dict[str, Any]]:
    """Place lead notes on an 8th/16th grid. Density controls attacks-per-bar."""
    if not pitches:
        return []

    target = DENSITY_NOTES_PER_BAR.get(dance_type, DENSITY_NOTES_PER_BAR["tango"])[density]
    # Slight role shaping without undoing density (old code capped tango at 2/bar)
    if density == "low" and role == "answer":
        target = max(2, target - 1)
    if phrase_end and density == "high":
        target = min(target + 1, beats_per_bar * 4)  # allow a little turn into the cadence

    if tonic is not None and mode is not None and symbol is not None:
        pitches = _expand_pitches_to_count(rng, pitches, target, tonic, mode, symbol)
    else:
        while len(pitches) < target:
            pitches.append(pitches[-1])
        pitches = pitches[:target]

    placements = _pick_grid_placements(
        rng,
        beats_per_bar=beats_per_bar,
        count=len(pitches),
        density=density,
        dance_type=dance_type,
    )
    notes: list[dict[str, Any]] = []
    for j, pitch in enumerate(pitches):
        start_local = placements[j] if j < len(placements) else 0.0
        is_last = j == len(pitches) - 1
        next_start = (
            placements[j + 1]
            if j + 1 < len(placements)
            else beats_per_bar
        )
        gap = max(0.05, next_start - start_local)
        # Dense levels: short articulations; low: more sustained
        if density == "high":
            dur = min(gap, 0.28 if not is_last else max(0.35, gap * 0.9))
        elif density == "medium":
            dur = min(gap * 0.95, gap if is_last else 0.45)
        else:
            dur = min(beats_per_bar - start_local, max(gap * 0.9, 0.5))
        if is_last and phrase_end and density != "high":
            dur = max(dur, min(beats_per_bar - start_local, 0.75))

        note: dict[str, Any] = {
            "pitch": int(pitch),
            "start_beat": round(bar * beats_per_bar + start_local, 3),
            "duration_beats": round(max(0.08, dur), 3),
            "phrase_role": role,
            "voice": voice,
        }
        if is_last and phrase_end:
            note["phrase_end"] = True
        notes.append(note)

        # High density: occasional 32nd neighbor (scale step, clamped)
        if (
            voice == "lead"
            and density == "high"
            and not is_last
            and gap >= 0.25
            and rng.random() < (0.28 if variation == "high" else 0.15)
        ):
            nbr = _clamp_melody(int(pitch + rng.choice([-1, 1, 2, -2])))
            if nbr != pitch:
                notes.append(
                    {
                        "pitch": nbr,
                        "start_beat": round(bar * beats_per_bar + start_local + 0.125, 3),
                        "duration_beats": 0.1,
                        "phrase_role": role,
                        "voice": "lead",
                    }
                )

    notes.sort(key=lambda n: n["start_beat"])
    return notes


def _intro_melody(
    rng: random.Random,
    *,
    start_bar: int,
    bars: int,
    beats_per_bar: int,
    tonic: int,
    mode: str,
    chords_for_bars: list[str],
    dance_type: str,
) -> list[dict[str, Any]]:
    """Groove only + tiny pickup — theme has not entered yet."""
    notes: list[dict[str, Any]] = []
    # Last 1–2 bars: short anacrusis into the theme
    for j in range(max(0, bars - 2), bars):
        symbol = chords_for_bars[j]
        chord = _chord_pool(tonic, mode, symbol)
        pitch = rng.choice(chord[1:] or chord)
        start_local = beats_per_bar * 0.5 if dance_type != "vals" else 2.0
        notes.append(
            {
                "pitch": int(pitch),
                "start_beat": round((start_bar + j) * beats_per_bar + start_local, 3),
                "duration_beats": round(beats_per_bar - start_local, 3),
                "phrase_role": "pickup",
                "voice": "fill",
            }
        )
    return notes


def _bridge_melody(
    rng: random.Random,
    *,
    start_bar: int,
    bars: int,
    beats_per_bar: int,
    tonic: int,
    mode: str,
    chords_for_bars: list[str],
) -> list[dict[str, Any]]:
    """Sparse rising line / silence — clears space before next theme entry."""
    notes: list[dict[str, Any]] = []
    for j in range(bars):
        if j % 2 == 1 and bars > 2:
            continue  # leave air
        symbol = chords_for_bars[j]
        chord = _chord_pool(tonic, mode, symbol)
        pitch = _clamp_melody(chord[-1] + (2 if j == bars - 1 else 0))
        notes.append(
            {
                "pitch": int(pitch),
                "start_beat": round((start_bar + j) * beats_per_bar, 3),
                "duration_beats": round(beats_per_bar * 0.9, 3),
                "phrase_role": "bridge",
                "voice": "fill",
                "phrase_end": j == bars - 1,
            }
        )
    return notes


def _coda_melody(
    rng: random.Random,
    *,
    start_bar: int,
    bars: int,
    beats_per_bar: int,
    tonic: int,
    mode: str,
    chords_for_bars: list[str],
    theme_cells: list[list[int]] | None,
    dance_type: str,
) -> list[dict[str, Any]]:
    """Theme tag (if we have one) then a long tonic cadence."""
    notes: list[dict[str, Any]] = []
    tag_bars = min(2, bars - 1) if bars > 1 else 0
    if theme_cells and tag_bars:
        for j in range(tag_bars):
            cell = theme_cells[j % len(theme_cells)]
            symbol = chords_for_bars[j]
            pitches = [
                _nearest(_chord_pool(tonic, mode, symbol), p) for p in cell[:2]
            ]
            notes.extend(
                _emit_bar_notes(
                    rng,
                    bar=start_bar + j,
                    beats_per_bar=beats_per_bar,
                    pitches=pitches,
                    density="low",
                    variation="low",
                    phrase_end=j == tag_bars - 1,
                    role="answer" if j == tag_bars - 1 else "question",
                    dance_type=dance_type,
                    voice="lead",
                    tonic=tonic,
                    mode=mode,
                    symbol=symbol,
                )
            )
    # Final cadence note on tonic
    last = bars - 1
    tonic_pitch = _clamp_melody(_chord_pool(tonic, mode, chords_for_bars[last])[0])
    notes.append(
        {
            "pitch": int(tonic_pitch),
            "start_beat": round((start_bar + last) * beats_per_bar, 3),
            "duration_beats": round(beats_per_bar * 1.5, 3),
            "phrase_role": "cadence",
            "voice": "lead",
            "phrase_end": True,
        }
    )
    return notes


def _annotate_drama(
    notes: list[dict[str, Any]],
    drama: dict[str, Any],
) -> list[dict[str, Any]]:
    pause = set(drama.get("pause_bars") or [])
    climax = set(drama.get("climax_bars") or [])
    dense = set(drama.get("dense_bars") or [])
    energy = drama.get("energy") or {}
    out: list[dict[str, Any]] = []
    for n in notes:
        bpb = int(n.pop("_bpb", 2)) or 2
        bar = int(float(n["start_beat"]) // bpb)
        if bar in pause and n.get("voice") == "lead":
            continue  # dramatic hole — drop lead note
        if bar in climax:
            # Lift register without stacking everything on the same top pitch
            p = int(n["pitch"])
            n["pitch"] = _clamp_melody(p + (12 if p <= 72 else 5))
            n["drama"] = "climax"
            n["duration_beats"] = round(float(n["duration_beats"]) * 1.15, 3)
        elif bar in dense:
            n["drama"] = "dense"
        else:
            n["drama"] = "normal"
        n["energy"] = energy.get(bar, 0.5)
        out.append(n)
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
    dance_type: str = "tango",
    theme_state: dict[str, Any] | None = None,
    drama: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    theme_state = theme_state if theme_state is not None else {}
    drama = drama or {}
    pause = set(drama.get("pause_bars") or [])
    dense = set(drama.get("dense_bars") or [])
    climax = set(drama.get("climax_bars") or [])

    if section_name == "intro":
        notes = _intro_melody(
            rng,
            start_bar=start_bar,
            bars=bars,
            beats_per_bar=beats_per_bar,
            tonic=tonic,
            mode=mode,
            chords_for_bars=chords_for_bars,
            dance_type=dance_type,
        )
        for n in notes:
            n["_bpb"] = beats_per_bar
        return _annotate_drama(notes, drama)
    if section_name == "bridge":
        notes = _bridge_melody(
            rng,
            start_bar=start_bar,
            bars=bars,
            beats_per_bar=beats_per_bar,
            tonic=tonic,
            mode=mode,
            chords_for_bars=chords_for_bars,
        )
        for n in notes:
            n["_bpb"] = beats_per_bar
        return _annotate_drama(notes, drama)
    if section_name == "coda":
        notes = _coda_melody(
            rng,
            start_bar=start_bar,
            bars=bars,
            beats_per_bar=beats_per_bar,
            tonic=tonic,
            mode=mode,
            chords_for_bars=chords_for_bars,
            theme_cells=theme_state.get("cells"),
            dance_type=dance_type,
        )
        for n in notes:
            n["_bpb"] = beats_per_bar
        return _annotate_drama(notes, drama)

    notes_per_bar = DENSITY_NOTES_PER_BAR.get(dance_type, DENSITY_NOTES_PER_BAR["tango"])[
        density
    ]
    var = VARIATION_STRENGTH[variation]
    if var >= 0.5 and rng.random() < var * 0.4:
        notes_per_bar = min(beats_per_bar * 4, notes_per_bar + 2)

    notes: list[dict[str, Any]] = []
    last_pitch: int | None = None
    question_memory: list[int] | None = None
    capture_theme = section_name == "A" and not theme_state.get("cells")
    # A_prime reuses theme less rigidly when variation is high
    reuse_theme = (
        section_name in ("A", "A_prime")
        and bool(theme_state.get("cells"))
        and not (section_name == "A_prime" and rng.random() < var * 0.55)
    )
    theme_cells: list[list[int]] = list(theme_state.get("cells") or [])
    captured: list[list[int]] = []
    theme_shift = rng.choice([-5, -3, -2, 0, 2, 3, 5]) if var >= 0.5 else 0

    i = 0
    cell_i = 0
    while i < bars:
        bar_q = start_bar + i
        # Dramatic pause bar — leave silence in the lead
        if bar_q in pause:
            i += 1
            continue

        local_density: Level = density
        local_n = notes_per_bar
        if bar_q in dense or bar_q in climax:
            local_density = "high"
            local_n = min(
                beats_per_bar * 4,
                DENSITY_NOTES_PER_BAR[dance_type]["high"] + (2 if bar_q in climax else 0),
            )

        symbol_q = chords_for_bars[i]
        is_pair = i + 1 < bars and (start_bar + i + 1) not in pause
        role_first: Literal["question", "answer"] = "question" if is_pair else "answer"
        # Contour seed length — emit expands to full per-bar density on the grid
        contour_n = min(4, max(2, local_n // 2))
        reg_q = _phrase_register_bias(
            rng,
            section_name=section_name,
            role=role_first,
            drama_high=bar_q in climax or bar_q in dense,
            variation=var,
        )

        if reuse_theme and cell_i < len(theme_cells):
            base = theme_cells[cell_i]
            shift = theme_shift if section_name == "A_prime" else 0
            shift += reg_q
            q_pitches = [
                _nearest(
                    _chord_pool(tonic, mode, symbol_q),
                    p + shift + rng.choice([0, 0, 2, -2, 3] if var > 0.5 else [0, 0, 2, -1]),
                )
                for p in base
            ]
            q_pitches = q_pitches[:contour_n]
            while len(q_pitches) < contour_n:
                prev = q_pitches[-1]
                step = [p for p in _scale_pool(tonic, mode) if 0 < abs(p - prev) <= 2]
                q_pitches.append(rng.choice(step) if step else _clamp_melody(prev + 2))
            cell_i += 1
        elif (
            question_memory
            and role_first == "question"
            and section_name in ("A_prime", "A", "B")
            and rng.random() > var
        ):
            q_pitches = [
                _nearest(_chord_pool(tonic, mode, symbol_q), p + rng.choice([0, 0, 2, -2, 4]))
                for p in question_memory
            ]
            q_pitches = q_pitches[:contour_n]
            while len(q_pitches) < contour_n:
                prev = q_pitches[-1]
                step = [p for p in _scale_pool(tonic, mode) if 0 < abs(p - prev) <= 2]
                q_pitches.append(rng.choice(step) if step else _clamp_melody(prev + 2))
        else:
            q_pitches = _phrase_contour(
                rng,
                n=contour_n,
                role=role_first,
                tonic=tonic,
                mode=mode,
                symbol=symbol_q,
                start_pitch=last_pitch,
                variation=var,
                register_bias=reg_q,
            )

        if role_first == "question":
            question_memory = list(q_pitches)
        if capture_theme:
            captured.append(list(q_pitches))

        emitted = _emit_bar_notes(
            rng,
            bar=bar_q,
            beats_per_bar=beats_per_bar,
            pitches=q_pitches,
            density=local_density,
            variation=variation,
            phrase_end=not is_pair,
            role=role_first,
            dance_type=dance_type,
            voice="lead",
            tonic=tonic,
            mode=mode,
            symbol=symbol_q,
        )
        for n in emitted:
            n["_bpb"] = beats_per_bar
        notes.extend(emitted)
        last_pitch = q_pitches[-1]
        i += 1

        if not is_pair:
            continue

        bar_a = start_bar + i
        if bar_a in pause:
            i += 1
            continue

        local_density = "high" if bar_a in dense or bar_a in climax else density
        local_n = notes_per_bar
        if bar_a in dense or bar_a in climax:
            local_n = min(
                beats_per_bar * 4,
                DENSITY_NOTES_PER_BAR[dance_type]["high"] + (2 if bar_a in climax else 0),
            )
        contour_n = min(4, max(2, local_n // 2))
        reg_a = _phrase_register_bias(
            rng,
            section_name=section_name,
            role="answer",
            drama_high=bar_a in climax or bar_a in dense,
            variation=var,
        )

        symbol_a = chords_for_bars[i]
        if reuse_theme and cell_i < len(theme_cells):
            base = theme_cells[cell_i]
            shift = (theme_shift if section_name == "A_prime" else 0) + reg_a
            a_pitches = [
                _nearest(_chord_pool(tonic, mode, symbol_a), p + shift) for p in base
            ]
            a_pitches = a_pitches[:contour_n]
            while len(a_pitches) < contour_n:
                prev = a_pitches[-1]
                step = [p for p in _scale_pool(tonic, mode) if 0 < abs(p - prev) <= 2]
                a_pitches.append(rng.choice(step) if step else _clamp_melody(prev - 2))
            cell_i += 1
        else:
            a_start = last_pitch
            if var > 0.3 and question_memory:
                a_start = list(reversed(question_memory))[0]
            a_pitches = _phrase_contour(
                rng,
                n=contour_n,
                role="answer",
                tonic=tonic,
                mode=mode,
                symbol=symbol_a,
                start_pitch=a_start,
                variation=var + (0.15 if section_name == "B" else 0),
                register_bias=reg_a,
            )
        if capture_theme:
            captured.append(list(a_pitches))

        emitted = _emit_bar_notes(
            rng,
            bar=bar_a,
            beats_per_bar=beats_per_bar,
            pitches=a_pitches,
            density=local_density,
            variation=variation,
            phrase_end=True,
            role="answer",
            dance_type=dance_type,
            voice="lead",
            tonic=tonic,
            mode=mode,
            symbol=symbol_a,
        )
        for n in emitted:
            n["_bpb"] = beats_per_bar
        notes.extend(emitted)
        last_pitch = a_pitches[-1]
        i += 1

    if capture_theme and captured:
        theme_state["cells"] = captured[:4]

    return _annotate_drama(notes, drama)


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

    if melody_density not in ("low", "medium", "high"):
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
    # Extra harmonic-rhythm variation (tango often flips between 1–2 bars/chord)
    if dance_type == "tango" and rng.random() < VARIATION_STRENGTH[melody_variation] * 0.45:
        bars_per_chord = 1 if bars_per_chord == 2 else 2

    drama = _build_drama_map(
        rng, sections, dance_type=dance_type, variation=melody_variation
    )

    chords: list[dict[str, Any]] = []
    melody: list[dict[str, Any]] = []
    form_labels: list[str] = []
    harmony_plan: list[dict[str, Any]] = []
    theme_state: dict[str, Any] = {}
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
        sec_bpc = int(sec.get("bars_per_chord") or bars_per_chord)
        prog_i = 0
        section_start_bar = bar
        for j in range(section_bars):
            if j % sec_bpc == 0:
                symbol = prog[prog_i % len(prog)]
                prog_i += 1
            else:
                symbol = section_symbols[-1] if section_symbols else prog[0]
            section_symbols.append(symbol)
            energy = float((drama.get("energy") or {}).get(bar, 0.5))
            tag = "normal"
            if bar in set(drama.get("climax_bars") or []):
                tag = "climax"
            elif bar in set(drama.get("pause_bars") or []):
                tag = "pause"
            elif bar in set(drama.get("dense_bars") or []):
                tag = "dense"
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
                    "drama": tag,
                    "energy": energy,
                }
            )
            bar += 1

        # What the listener actually hears (collapse held repeats) — not the unused template tail
        realized: list[str] = []
        for sym in section_symbols:
            if not realized or realized[-1] != sym:
                realized.append(sym)
        sec["bar_from"] = section_start_bar + 1  # 1-based for UI
        sec["bar_to"] = bar
        sec["progression_template"] = list(prog)
        sec["progression"] = realized

        dens: Level = melody_density
        if section_name == "B" and melody_density == "high":
            dens = "medium"

        melody.extend(
            _melody_for_section(
                rng,
                start_bar=section_start_bar,
                bars=section_bars,
                beats_per_bar=beats_per_bar,
                tonic=int(sec["tonic"]),
                mode=str(sec["mode"]),
                chords_for_bars=section_symbols,
                density=dens,
                variation=melody_variation,
                section_name=section_name,
                dance_type=dance_type,
                theme_state=theme_state,
                drama=drama,
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
        "drama": {
            "climax_bars": [b + 1 for b in drama["climax_bars"]],
            "pause_bars": [b + 1 for b in drama["pause_bars"]],
            "dense_bars": [b + 1 for b in drama["dense_bars"]],
        },
        "melody_density": melody_density,
        "melody_variation": melody_variation,
        "bars": total_bars,
        "chords": chords,
        "melody": melody,
    }
