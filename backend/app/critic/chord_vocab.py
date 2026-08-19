"""Expected chord spellings for CHORD_SPELLING_INVALID (M1-aligned expert prior)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ChordSpec:
    symbol: str
    root_semitones: int
    intervals: tuple[int, ...]


# Symbols the current engine may emit — spellings match M1 target, not buggy harmony.py.
MINOR_VOCAB: dict[str, ChordSpec] = {
    "i": ChordSpec("i", 0, (0, 3, 7)),
    "ii": ChordSpec("ii", 2, (0, 3, 7)),
    "iiø": ChordSpec("iiø", 2, (0, 3, 6, 10)),
    "iii": ChordSpec("iii", 3, (0, 4, 7)),
    "III": ChordSpec("III", 3, (0, 4, 7)),
    "iv": ChordSpec("iv", 5, (0, 3, 7)),
    "IV": ChordSpec("IV", 5, (0, 4, 7)),
    "V": ChordSpec("V", 7, (0, 4, 7)),
    "V7": ChordSpec("V7", 7, (0, 4, 7, 10)),
    "V7b9": ChordSpec("V7b9", 7, (0, 4, 7, 10, 13)),
    "vi": ChordSpec("vi", 9, (0, 3, 7)),
    "VI": ChordSpec("VI", 8, (0, 4, 7)),
    "VII": ChordSpec("VII", 10, (0, 4, 7)),  # natural-minor bVII (G–B–D in A minor)
    "bVII": ChordSpec("bVII", 10, (0, 4, 7)),
    "vii°": ChordSpec("vii°", 11, (0, 3, 6)),
}

MAJOR_VOCAB: dict[str, ChordSpec] = {
    "I": ChordSpec("I", 0, (0, 4, 7)),
    "ii": ChordSpec("ii", 2, (0, 3, 7)),
    "iii": ChordSpec("iii", 4, (0, 3, 7)),
    "IV": ChordSpec("IV", 5, (0, 4, 7)),
    "V": ChordSpec("V", 7, (0, 4, 7)),
    "V7": ChordSpec("V7", 7, (0, 4, 7, 10)),
    "V7b9": ChordSpec("V7b9", 7, (0, 4, 7, 10, 13)),
    "vi": ChordSpec("vi", 9, (0, 3, 7)),
    "vii°": ChordSpec("vii°", 11, (0, 3, 6)),
    "i": ChordSpec("i", 0, (0, 3, 7)),  # borrowed minor tonic
    "iv": ChordSpec("iv", 5, (0, 3, 7)),
}


def expected_pitch_classes(tonic: int, mode: str, symbol: str) -> frozenset[int] | None:
    vocab = MINOR_VOCAB if mode == "minor" else MAJOR_VOCAB
    spec = vocab.get(symbol)
    if spec is None:
        return None
    root_pc = (tonic + spec.root_semitones) % 12
    return frozenset((root_pc + iv) % 12 for iv in spec.intervals)
