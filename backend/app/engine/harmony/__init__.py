"""Harmony: legacy templates + M5 functional grammar."""

from __future__ import annotations

from app.engine.harmony.grammar import (
    CHORD_CHOICE,
    FUNCTION_TRANSITIONS,
    pick_chord_for_function,
    pick_function_transition,
)
from app.engine.harmony.legacy import (
    HARMONIC_MINOR,
    MAJOR_SCALE,
    MINOR_SCALE,
    PROGRESSIONS_MAJOR,
    PROGRESSIONS_MINOR,
    TONICS,
    UnknownChordSymbol,
    build_chord_plan,
    chord_pitches,
    normalize_symbol,
    pick_key,
    pick_progression,
    relative_key,
)

__all__ = [
    "CHORD_CHOICE",
    "FUNCTION_TRANSITIONS",
    "HARMONIC_MINOR",
    "MAJOR_SCALE",
    "MINOR_SCALE",
    "PROGRESSIONS_MAJOR",
    "PROGRESSIONS_MINOR",
    "TONICS",
    "UnknownChordSymbol",
    "build_chord_plan",
    "chord_pitches",
    "normalize_symbol",
    "pick_chord_for_function",
    "pick_function_transition",
    "pick_key",
    "pick_progression",
    "relative_key",
]
