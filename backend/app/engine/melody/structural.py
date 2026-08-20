"""Pass 1 — structural goal tones and backbone contour (M4)."""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Any, Protocol

from app.engine.harmony import HARMONIC_MINOR, MAJOR_SCALE, chord_pitches

MELODY_LO = 55  # G3
MELODY_HI = 96  # C7

CONTOUR_WEIGHTS: dict[str, dict[str, float]] = {
    "tango": {
        "descent": 0.32,
        "arch": 0.20,
        "plateau": 0.20,
        "leap_fill": 0.16,
        "ascent": 0.12,
    },
    "vals": {
        "arch": 0.34,
        "ascent": 0.26,
        "descent": 0.24,
        "leap_fill": 0.12,
        "plateau": 0.04,
    },
    "milonga": {
        "plateau": 0.34,
        "descent": 0.26,
        "arch": 0.20,
        "leap_fill": 0.12,
        "ascent": 0.08,
    },
}


@dataclass
class StructuralNote:
    pitch: int
    bar: int  # relative to phrase start (0-based)
    beat: float  # strong beat: 0.0 or beats_per_bar/2
    is_goal: bool
    chord_degree: int  # 1/3/5/7


class PhraseLike(Protocol):
    bars: int
    cadence: str


@dataclass
class ChordSlot:
    symbol: str
    tonic: int
    mode: str


def clamp_melody(p: int) -> int:
    while p < MELODY_LO:
        p += 12
    while p > MELODY_HI:
        p -= 12
    return p


def chord_pool(tonic: int, mode: str, symbol: str) -> list[int]:
    return [
        clamp_melody(p + oct_)
        for p in chord_pitches(tonic, mode, symbol)
        for oct_ in (0, 12, 24)
    ]


def scale_pool(tonic: int, mode: str) -> list[int]:
    intervals = HARMONIC_MINOR if mode == "minor" else MAJOR_SCALE
    return [
        clamp_melody(tonic + iv + oct_ * 12)
        for oct_ in (-1, 0, 1, 2)
        for iv in intervals
    ]


def nearest(pool: list[int], target: int) -> int:
    return min(pool, key=lambda p: abs(p - target))


def _pc(p: int) -> int:
    return int(p) % 12


def _degree_pitch(pool: list[int], root_pc: int, degree: int, near: int) -> int:
    """Pick chord tone by degree (1=root, 3=third, 5=fifth, 7=seventh) near target."""
    # Sort unique PCs in chord by interval above root
    pcs = sorted({_pc(p) for p in pool})
    if not pcs:
        return clamp_melody(near)
    rel = sorted(((pc - root_pc) % 12, pc) for pc in pcs)
    # Map degree → preferred chord-tone index
    if degree == 1:
        want_rel = 0
    elif degree == 3:
        want_rel = next((r for r, _ in rel if r in (3, 4)), rel[min(1, len(rel) - 1)][0])
    elif degree == 5:
        want_rel = next((r for r, _ in rel if r in (6, 7)), rel[min(2, len(rel) - 1)][0])
    else:  # 7
        want_rel = next((r for r, _ in rel if r in (10, 11)), rel[-1][0])
    target_pc = (root_pc + want_rel) % 12
    candidates = [p for p in pool if _pc(p) == target_pc] or pool
    return nearest(candidates, near)


def _goal_for_cadence(
    cadence: str,
    chords: list[ChordSlot],
    *,
    near: int,
    register_bias: int,
) -> tuple[int, int]:
    """Return (pitch, chord_degree) for phrase goal from cadence type."""
    last = chords[-1]
    pool = chord_pool(last.tonic, last.mode, last.symbol)
    root_pc = _pc(chord_pitches(last.tonic, last.mode, last.symbol)[0])
    band = near + register_bias
    cad = (cadence or "authentic").lower()
    if cad in ("authentic", "open"):
        return _degree_pitch(pool, root_pc, 1, band), 1
    if cad == "imperfect":
        deg = 3 if abs(band - _degree_pitch(pool, root_pc, 3, band)) <= abs(
            band - _degree_pitch(pool, root_pc, 5, band)
        ) else 5
        return _degree_pitch(pool, root_pc, deg, band), deg
    if cad == "half":
        # Prefer leading-tone (3 of V) or root
        deg = 3 if "V" in last.symbol else 1
        return _degree_pitch(pool, root_pc, deg, band), deg
    if cad == "deceptive":
        return _degree_pitch(pool, root_pc, 3, band), 3
    return _degree_pitch(pool, root_pc, 1, band), 1


def _pick_contour(rng: random.Random, dance_type: str, prefer: str | None = None) -> str:
    if prefer and prefer in CONTOUR_WEIGHTS.get(dance_type, {}):
        # Soft preference: 50% force preferred when available
        if rng.random() < 0.5:
            return prefer
    weights = CONTOUR_WEIGHTS.get(dance_type, CONTOUR_WEIGHTS["tango"])
    names = list(weights.keys())
    ws = [weights[n] for n in names]
    return rng.choices(names, weights=ws, k=1)[0]


def _strong_beats(beats_per_bar: float) -> list[float]:
    mid = beats_per_bar / 2.0
    if beats_per_bar >= 2.9:  # vals 3/4
        return [0.0, 1.0]  # beat 1 and sometimes 2 as structural
    return [0.0, mid]


def _degree_sequence(contour: str, n: int) -> list[int]:
    """Chord-degree outline for backbone (1/3/5/8)."""
    templates = {
        "descent": [5, 4, 3, 2, 1],
        "arch": [1, 3, 5, 3, 1],
        "ascent": [1, 3, 5],
        "plateau": [5, 5, 4, 3],
        "leap_fill": [1, 8, 5, 3, 1],
    }
    seq = list(templates.get(contour, templates["arch"]))
    if n <= len(seq):
        # Keep start and goal, subsample middle
        if n == 1:
            return [seq[-1]]
        if n == 2:
            return [seq[0], seq[-1]]
        idxs = [0] + [round(i * (len(seq) - 1) / (n - 1)) for i in range(1, n - 1)] + [len(seq) - 1]
        return [seq[i] for i in idxs]
    while len(seq) < n:
        seq.insert(-1, seq[-2] if len(seq) > 1 else 3)
    return seq[:n]


def _bar_positions(n_struct: int, n_bars: int, beats_per_bar: float, rng: random.Random) -> list[tuple[int, float]]:
    """Place structural notes on strong beats across the phrase."""
    strong = _strong_beats(beats_per_bar)
    if n_struct == 1:
        return [(n_bars - 1, 0.0)]
    positions: list[tuple[int, float]] = []
    # Always start near beginning, end on last bar downbeat
    positions.append((0, 0.0))
    if n_struct == 2:
        positions.append((n_bars - 1, 0.0))
        return positions
    # Middle anchors evenly in remaining bars
    mid_count = n_struct - 2
    for i in range(mid_count):
        t = (i + 1) / (mid_count + 1)
        bar = min(n_bars - 1, max(0, int(round(t * (n_bars - 1)))))
        beat = strong[1] if (i % 2 == 0 and len(strong) > 1 and rng.random() < 0.45) else 0.0
        # Avoid colliding with start/end
        if bar == 0:
            bar = 1 if n_bars > 2 else 0
            beat = strong[-1] if bar == 0 else beat
        if bar == n_bars - 1 and beat == 0.0:
            bar = max(0, n_bars - 2)
        positions.append((bar, beat))
    positions.append((n_bars - 1, 0.0))
    # Sort and uniquify
    positions = sorted(set(positions), key=lambda x: (x[0], x[1]))
    while len(positions) < n_struct:
        b = rng.randrange(n_bars)
        positions.append((b, 0.0))
        positions = sorted(set(positions), key=lambda x: (x[0], x[1]))
    return positions[:n_struct]


def plan_structural_line(
    phrase: PhraseLike | Any,
    chords: list[ChordSlot],
    *,
    dance_type: str = "tango",
    prev_end: int | None = None,
    rng: random.Random,
    beats_per_bar: float = 2.0,
    register_bias: int = 0,
    prefer_contour: str | None = None,
    pitch_cell_intervals: list[int] | None = None,
) -> list[StructuralNote]:
    """Plan 2–4 structural notes forming a singable backbone."""
    n_bars = max(1, int(getattr(phrase, "bars", 4)))
    cadence = str(getattr(phrase, "cadence", "authentic") or "authentic")
    if len(chords) < n_bars:
        # Pad with last chord
        last = chords[-1] if chords else ChordSlot("i", 57, "minor")
        chords = list(chords) + [last] * (n_bars - len(chords))
    chords = chords[:n_bars]

    contour = _pick_contour(rng, dance_type, prefer_contour)
    # Phrase length drives structural count
    if n_bars <= 2:
        n_struct = 2
    elif n_bars <= 4:
        n_struct = rng.choice([3, 3, 4])
    else:
        n_struct = rng.choice([3, 4, 4])

    degrees = _degree_sequence(contour, n_struct)
    positions = _bar_positions(n_struct, n_bars, beats_per_bar, rng)

    start_chord = chords[0]
    start_pool = chord_pool(start_chord.tonic, start_chord.mode, start_chord.symbol)
    start_root = _pc(chord_pitches(start_chord.tonic, start_chord.mode, start_chord.symbol)[0])

    if prev_end is not None:
        start_near = prev_end
        # Stay within ≤5 semitones of previous phrase end
        close = [p for p in start_pool if abs(p - prev_end) <= 5]
        if close:
            start_pitch = nearest(close, prev_end + register_bias)
        else:
            start_pitch = nearest(start_pool, prev_end + register_bias)
            if abs(start_pitch - prev_end) > 5:
                # Step from prev_end toward nearest chord tone
                direction = 1 if start_pitch > prev_end else -1
                start_pitch = clamp_melody(prev_end + direction * min(5, abs(start_pitch - prev_end)))
                start_pitch = nearest(start_pool, start_pitch)
    else:
        start_pitch = _degree_pitch(
            start_pool, start_root, degrees[0] if degrees[0] != 8 else 1, 67 + register_bias
        )

    goal_pitch, goal_deg = _goal_for_cadence(
        cadence, chords, near=start_pitch + register_bias, register_bias=register_bias
    )
    degrees[-1] = goal_deg

    # Optional: bias middle pitches toward pitch-cell contour shape
    cell_shape = pitch_cell_intervals

    notes: list[StructuralNote] = []
    for i, ((bar, beat), deg) in enumerate(zip(positions, degrees)):
        slot = chords[min(bar, len(chords) - 1)]
        pool = chord_pool(slot.tonic, slot.mode, slot.symbol)
        root_pc = _pc(chord_pitches(slot.tonic, slot.mode, slot.symbol)[0])
        is_goal = i == len(positions) - 1
        is_start = i == 0

        if is_start:
            pitch = start_pitch
            use_deg = degrees[0] if degrees[0] != 8 else 1
        elif is_goal:
            pitch = goal_pitch
            use_deg = goal_deg
        else:
            use_deg = 1 if deg == 8 else deg
            # Leap_fill middle may target octave
            if deg == 8:
                octave_cands = [p for p in pool if _pc(p) == root_pc and p >= start_pitch + 7]
                pitch = nearest(octave_cands or pool, start_pitch + 12)
            else:
                ref = notes[-1].pitch if notes else start_pitch
                if cell_shape and len(cell_shape) > i:
                    target = start_pitch + cell_shape[i]
                    pitch = _degree_pitch(pool, root_pc, use_deg, target)
                else:
                    pitch = _degree_pitch(pool, root_pc, use_deg, ref)
            # Plateau: declamación unisons (~piece-level repeated_note_ratio 0.10–0.20)
            if contour == "plateau" and notes and rng.random() < 0.42:
                same = [p for p in pool if _pc(p) == _pc(notes[-1].pitch)]
                if same:
                    pitch = nearest(same, notes[-1].pitch)

        notes.append(
            StructuralNote(
                pitch=clamp_melody(pitch),
                bar=bar,
                beat=float(beat),
                is_goal=is_goal,
                chord_degree=use_deg if not is_goal else goal_deg,
            )
        )

    # Force goal pitch on last
    notes[-1].pitch = clamp_melody(goal_pitch)
    notes[-1].is_goal = True
    notes[-1].chord_degree = goal_deg
    return notes
