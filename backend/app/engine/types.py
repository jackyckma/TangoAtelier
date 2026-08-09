from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class NoteEvent:
    pitch: int
    start: float  # seconds
    duration: float
    velocity: int
    track: str


@dataclass
class ChordEvent:
    bar: int
    symbol: str
    start: float
    duration: float


@dataclass
class PieceDraft:
    orchestra_id: str
    seed: int
    bpm: float
    key_name: str
    mode: str  # "minor" | "major"
    time_signature: tuple[int, int]
    rhythm_pattern: str
    form: list[str]
    notes: list[NoteEvent] = field(default_factory=list)
    chords: list[ChordEvent] = field(default_factory=list)
    bars: int = 0
