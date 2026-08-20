"""Non-chord-tone classifications for melody notes (M4)."""

from __future__ import annotations

from enum import Enum


class NCT(str, Enum):
    CHORD_TONE = "chord_tone"
    PASSING = "passing"
    NEIGHBOR = "neighbor"
    APPOGGIATURA = "appoggiatura"
    SUSPENSION = "suspension"
    ANTICIPATION = "anticipation"
    ESCAPE = "escape"
    CHROMATIC = "chromatic"
