"""M6 motivic development techniques (pure contract — not wired into skeleton yet)."""

from __future__ import annotations

import random
from dataclasses import dataclass
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


MELODIC_SECTIONS = frozenset(
    {"A", "B", "A_prime", "variacion", "bridge", "intro", "coda"}
)


@dataclass(frozen=True)
class MotifPlan:
    cell_id: str
    first_appearance: int
    developments: list[tuple[int, DevelopmentTechnique]]
    payoff_bar: int
    payoff_technique: DevelopmentTechnique


def pitch_cell_similarity(intervals_a: list[int], intervals_b: list[int]) -> float:
    """Return similarity in [0, 1] between two pitch-cell interval lists."""
    if not intervals_a and not intervals_b:
        return 1.0
    if not intervals_a or not intervals_b:
        return 0.0

    n = min(len(intervals_a), len(intervals_b))
    scores: list[float] = []
    for ia, ib in zip(intervals_a[:n], intervals_b[:n]):
        if ia == ib:
            scores.append(1.0)
        elif ia != 0 and ib != 0 and ia * ib < 0:
            scores.append(0.0)
        else:
            span = max(abs(ia), abs(ib), 1)
            scores.append(max(0.0, 1.0 - abs(ia - ib) / (2 * span)))
    return sum(scores) / len(scores)


def _section_spans(
    section_timeline: list[tuple[str, int]],
) -> dict[str, list[tuple[int, int]]]:
    spans: dict[str, list[tuple[int, int]]] = {}
    bar = 0
    for name, n in section_timeline:
        spans.setdefault(name, []).append((bar, bar + n))
        bar += n
    return spans


def _phrase_start_bars(start: int, end: int, n_phrases: int = 4) -> list[int]:
    length = end - start
    if length <= 0:
        return []
    phrase_len = max(1, length // n_phrases)
    return [start + i * phrase_len for i in range(n_phrases) if start + i * phrase_len < end]


def _first_appearance_bar(
    spans: dict[str, list[tuple[int, int]]],
    section_timeline: list[tuple[str, int]],
    cell_index: int,
) -> int:
    intro = spans.get("intro") or []
    a_spans = spans.get("A") or []
    b_spans = spans.get("B") or []

    if cell_index == 0:
        if intro:
            return intro[0][1] - 1
        if a_spans:
            return a_spans[0][0]
        return 0

    if b_spans:
        return b_spans[0][0]
    for name, _ in section_timeline:
        if name in ("B", "bridge", "variacion"):
            sec = spans.get(name)
            if sec:
                return sec[0][0]
    if a_spans:
        return a_spans[0][0] + 4
    return 0


def _sections_for_cell(cell_index: int) -> frozenset[str]:
    if cell_index == 0:
        return frozenset({"intro", "A", "A_prime", "coda"})
    return frozenset({"B", "bridge", "variacion", "A_prime"})


def _payoff_bar(
    rng: random.Random,
    spans: dict[str, list[tuple[int, int]]],
    climax_bar: int,
) -> int:
    coda = spans.get("coda") or []
    if rng.random() < 0.7:
        return int(climax_bar)
    if coda:
        return coda[0][0]
    return int(climax_bar)


def plan_motif_developments(
    motivic_cells: list[dict],
    section_timeline: list[tuple[str, int]],
    climax_bar: int,
    rng: random.Random,
) -> list[MotifPlan]:
    """Schedule setup, phrase-level developments, and climax-aligned payoff per cell."""
    if not motivic_cells:
        return []

    spans = _section_spans(section_timeline)
    payoff_techniques = (
        DevelopmentTechnique.AUGMENTATION,
        DevelopmentTechnique.ORNAMENTATION,
    )
    plans: list[MotifPlan] = []

    for idx, _cell in enumerate(motivic_cells):
        cell_id = str(idx)
        first_bar = _first_appearance_bar(spans, section_timeline, idx)
        allowed = _sections_for_cell(idx)
        developments: list[tuple[int, DevelopmentTechnique]] = []

        for section_name, sec_spans in spans.items():
            if section_name not in allowed or section_name not in MELODIC_SECTIONS:
                continue
            for start, end in sec_spans:
                phrase_starts = _phrase_start_bars(start, end)
                for phrase_i, bar in enumerate(phrase_starts):
                    if bar < first_bar:
                        continue
                    tech = technique_for_phrase(section_name, phrase_i, len(phrase_starts))
                    developments.append((bar, tech))

        developments.sort(key=lambda item: item[0])
        payoff_bar = _payoff_bar(rng, spans, climax_bar)
        payoff_technique = rng.choice(payoff_techniques)

        plans.append(
            MotifPlan(
                cell_id=cell_id,
                first_appearance=first_bar,
                developments=developments,
                payoff_bar=payoff_bar,
                payoff_technique=payoff_technique,
            )
        )

    return plans
