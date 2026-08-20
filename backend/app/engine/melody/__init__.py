"""M4 three-pass melody: structural → connect → decorate."""

from __future__ import annotations

from app.engine.melody.connect import (
    DENSITY_NOTES_PER_BAR,
    MelodyNote,
    generate_phrase_melody,
    melody_notes_to_dicts,
    plan_rests,
)
from app.engine.melody.decorate import decorate_melody_events
from app.engine.melody.nct import NCT
from app.engine.melody.rhythm_cell import (
    PitchCell,
    RhythmCell,
    TANGO_RHYTHM_CELLS,
    intervals_to_adjacent_steps,
    make_pitch_cell,
    sample_piece_cells,
    sample_rhythm_cell,
)
from app.engine.melody.structural import (
    MELODY_HI,
    MELODY_LO,
    ChordSlot,
    StructuralNote,
    clamp_melody,
    plan_structural_line,
)

__all__ = [
    "NCT",
    "MelodyNote",
    "StructuralNote",
    "ChordSlot",
    "RhythmCell",
    "PitchCell",
    "TANGO_RHYTHM_CELLS",
    "DENSITY_NOTES_PER_BAR",
    "MELODY_LO",
    "MELODY_HI",
    "clamp_melody",
    "plan_structural_line",
    "plan_rests",
    "generate_phrase_melody",
    "melody_notes_to_dicts",
    "decorate_melody_events",
    "sample_piece_cells",
    "sample_rhythm_cell",
    "make_pitch_cell",
    "intervals_to_adjacent_steps",
]
