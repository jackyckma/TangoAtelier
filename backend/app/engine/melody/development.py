"""M6 motivic development techniques (pure contract — not wired into skeleton yet)."""

from __future__ import annotations

from enum import Enum


class DevelopmentTechnique(str, Enum):
    LITERAL = "literal"
    SEQUENCE = "sequence"
    INVERSION = "inversion"
    AUGMENTATION = "augmentation"
    DIMINUTION = "diminution"
    FRAGMENTATION = "fragmentation"
    EXTENSION = "extension"
    ORNAMENTATION = "ornamentation"
    REHARMONIZATION = "reharmonization"
    RHYTHM_SWAP = "rhythm_swap"
    PITCH_SWAP = "pitch_swap"


SECTION_TECHNIQUES: dict[str, list[DevelopmentTechnique]] = {
    "A": [
        DevelopmentTechnique.LITERAL,
        DevelopmentTechnique.SEQUENCE,
        DevelopmentTechnique.LITERAL,
        DevelopmentTechnique.EXTENSION,
    ],
    "B": [
        DevelopmentTechnique.PITCH_SWAP,
        DevelopmentTechnique.SEQUENCE,
        DevelopmentTechnique.FRAGMENTATION,
        DevelopmentTechnique.EXTENSION,
    ],
    "A_prime": [
        DevelopmentTechnique.ORNAMENTATION,
        DevelopmentTechnique.SEQUENCE,
        DevelopmentTechnique.REHARMONIZATION,
        DevelopmentTechnique.ORNAMENTATION,
    ],
    "variacion": [
        DevelopmentTechnique.DIMINUTION,
        DevelopmentTechnique.DIMINUTION,
        DevelopmentTechnique.FRAGMENTATION,
        DevelopmentTechnique.DIMINUTION,
    ],
    "coda": [
        DevelopmentTechnique.FRAGMENTATION,
        DevelopmentTechnique.AUGMENTATION,
    ],
    "bridge": [
        DevelopmentTechnique.FRAGMENTATION,
        DevelopmentTechnique.RHYTHM_SWAP,
    ],
}


def technique_for_phrase(
    section_name: str,
    phrase_index: int,
    n_phrases: int,
) -> DevelopmentTechnique:
    """Return the development technique for a phrase, cycling the section list."""
    techniques = SECTION_TECHNIQUES.get(section_name)
    if not techniques:
        techniques = SECTION_TECHNIQUES["A"]
    if n_phrases <= 0:
        n_phrases = len(techniques)
    return techniques[phrase_index % len(techniques)]
