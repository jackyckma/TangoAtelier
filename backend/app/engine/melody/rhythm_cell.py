"""Rhythm and pitch motivic cells — freely paired (M4)."""

from __future__ import annotations

import random
from dataclasses import dataclass, field


@dataclass(frozen=True)
class RhythmCell:
    id: str
    onsets: list[float]
    durations: list[float]
    anacrusis: float
    accent_pattern: list[bool] = field(default_factory=list)


@dataclass(frozen=True)
class PitchCell:
    id: str
    intervals: list[int]  # relative to first pitch (not adjacent steps)
    contour_name: str


TANGO_RHYTHM_CELLS: list[RhythmCell] = [
    RhythmCell(
        "upbeat_3",
        onsets=[0.0, 0.5, 1.0],
        durations=[0.5, 0.5, 1.0],
        anacrusis=0.5,
        accent_pattern=[False, False, True],
    ),
    RhythmCell(
        "declaim",
        onsets=[0.0, 0.5, 1.0, 1.5],
        durations=[0.5, 0.5, 0.5, 0.5],
        anacrusis=1.0,
        accent_pattern=[True, False, True, False],
    ),
    RhythmCell(
        "long_short",
        onsets=[0.0, 1.5],
        durations=[1.5, 0.5],
        anacrusis=0.0,
        accent_pattern=[True, False],
    ),
    RhythmCell(
        "syncopa",
        onsets=[0.0, 0.75, 1.5],
        durations=[0.75, 0.75, 0.5],
        anacrusis=0.5,
        accent_pattern=[True, False, True],
    ),
    RhythmCell(
        "held",
        onsets=[0.0],
        durations=[2.0],
        anacrusis=0.5,
        accent_pattern=[True],
    ),
    RhythmCell(
        "332",
        onsets=[0.0, 0.75, 1.5],
        durations=[0.75, 0.75, 0.5],
        anacrusis=0.0,
        accent_pattern=[True, False, True],
    ),
]

VALS_RHYTHM_CELLS: list[RhythmCell] = [
    RhythmCell(
        "vals_smooth",
        onsets=[0.0, 1.0, 2.0],
        durations=[1.0, 1.0, 1.0],
        anacrusis=0.0,
        accent_pattern=[True, False, False],
    ),
    RhythmCell(
        "vals_long",
        onsets=[0.0, 2.0],
        durations=[2.0, 1.0],
        anacrusis=0.0,
        accent_pattern=[True, False],
    ),
    RhythmCell(
        "vals_pickup",
        onsets=[1.0, 2.0],
        durations=[1.0, 1.0],
        anacrusis=1.0,
        accent_pattern=[False, True],
    ),
    RhythmCell(
        "vals_held",
        onsets=[0.0],
        durations=[3.0],
        anacrusis=0.0,
        accent_pattern=[True],
    ),
]

MILONGA_RHYTHM_CELLS: list[RhythmCell] = [
    RhythmCell(
        "habanera",
        onsets=[0.0, 0.75, 1.0, 1.5],
        durations=[0.75, 0.25, 0.5, 0.5],
        anacrusis=0.0,
        accent_pattern=[True, False, True, False],
    ),
    RhythmCell(
        "milonga_332",
        onsets=[0.0, 0.75, 1.5],
        durations=[0.75, 0.75, 0.5],
        anacrusis=0.0,
        accent_pattern=[True, False, True],
    ),
    RhythmCell(
        "milonga_held",
        onsets=[0.0],
        durations=[2.0],
        anacrusis=0.5,
        accent_pattern=[True],
    ),
    RhythmCell(
        "milonga_long_short",
        onsets=[0.0, 1.5],
        durations=[1.5, 0.5],
        anacrusis=0.0,
        accent_pattern=[True, False],
    ),
    RhythmCell(
        "milonga_upbeat",
        onsets=[0.0, 0.5, 1.0],
        durations=[0.5, 0.5, 1.0],
        anacrusis=0.5,
        accent_pattern=[False, False, True],
    ),
]

# Contour → interval templates (relative to head). Used as PitchCell DNA.
_PITCH_TEMPLATES: dict[str, list[list[int]]] = {
    "descent": [[0, -2, -4, -5, -7], [0, -3, -5, -7], [0, -2, -5]],
    "arch": [[0, 3, 7, 3, 0], [0, 4, 7, 4, 0], [0, 2, 5, 2]],
    "ascent": [[0, 2, 4, 7], [0, 3, 5, 7], [0, 2, 5]],
    "plateau": [[0, 0, -2, -3], [0, 0, 0, -2], [0, 0, -1, -3]],
    "leap_fill": [[0, 12, 7, 5, 0], [0, 7, 5, 3, 0], [0, -7, -5, -3, 0]],
}


def rhythm_pool(dance_type: str) -> list[RhythmCell]:
    if dance_type == "vals":
        return VALS_RHYTHM_CELLS
    if dance_type == "milonga":
        return MILONGA_RHYTHM_CELLS
    return TANGO_RHYTHM_CELLS


def _sample_tango_rhythm(rng: random.Random) -> RhythmCell:
    """Bias so anacrusis > 0 appears in ≥ half of tango draws."""
    pool = TANGO_RHYTHM_CELLS
    with_up = [c for c in pool if c.anacrusis > 0]
    without = [c for c in pool if c.anacrusis <= 0]
    if rng.random() < 0.55 and with_up:
        return rng.choice(with_up)
    return rng.choice(without or pool)


def sample_rhythm_cell(rng: random.Random, dance_type: str) -> RhythmCell:
    if dance_type == "tango":
        return _sample_tango_rhythm(rng)
    return rng.choice(rhythm_pool(dance_type))


def make_pitch_cell(
    rng: random.Random,
    contour_name: str,
    *,
    cell_id: str | None = None,
) -> PitchCell:
    templates = _PITCH_TEMPLATES.get(contour_name) or _PITCH_TEMPLATES["arch"]
    intervals = list(rng.choice(templates))
    return PitchCell(
        id=cell_id or f"{contour_name}_{rng.randint(0, 9999)}",
        intervals=intervals,
        contour_name=contour_name,
    )


def sample_piece_cells(
    rng: random.Random,
    dance_type: str,
    *,
    n_rhythm: int | None = None,
    n_pitch: int | None = None,
    contours: list[str] | None = None,
) -> tuple[list[RhythmCell], list[PitchCell]]:
    """Roll 2–3 rhythm cells and 2–3 pitch cells for one piece."""
    nr = n_rhythm if n_rhythm is not None else rng.choice([2, 2, 3])
    np_ = n_pitch if n_pitch is not None else rng.choice([2, 2, 3])
    rhythms: list[RhythmCell] = []
    seen_r: set[str] = set()
    for _ in range(nr * 3):
        if len(rhythms) >= nr:
            break
        cell = sample_rhythm_cell(rng, dance_type)
        if cell.id not in seen_r or len(seen_r) >= len(rhythm_pool(dance_type)):
            rhythms.append(cell)
            seen_r.add(cell.id)
    while len(rhythms) < nr:
        rhythms.append(sample_rhythm_cell(rng, dance_type))

    # Ensure breath cells present when tango/milonga
    if dance_type in ("tango", "milonga"):
        ids = {c.id for c in rhythms}
        if "held" not in ids and "milonga_held" not in ids:
            held = next(c for c in rhythm_pool(dance_type) if "held" in c.id)
            rhythms[rng.randrange(len(rhythms))] = held
        if not any("long_short" in c.id for c in rhythms) and dance_type == "tango":
            ls = next(c for c in TANGO_RHYTHM_CELLS if c.id == "long_short")
            if len(rhythms) >= 2:
                rhythms[-1] = ls

    contour_pool = contours or ["descent", "arch", "ascent", "plateau", "leap_fill"]
    pitches: list[PitchCell] = []
    used: set[str] = set()
    for i in range(np_):
        prefer = [c for c in contour_pool if c not in used] or contour_pool
        name = rng.choice(prefer)
        used.add(name)
        pitches.append(make_pitch_cell(rng, name, cell_id=f"cell{i}_{name}"))
    return rhythms, pitches


def intervals_to_adjacent_steps(intervals: list[int]) -> list[int]:
    """Convert absolute-from-head intervals to adjacent steps (motif DNA)."""
    if not intervals:
        return []
    steps: list[int] = []
    prev = intervals[0]
    for iv in intervals[1:]:
        steps.append(iv - prev)
        prev = iv
    return steps
