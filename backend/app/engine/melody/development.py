"""M6 motivic development techniques and phrase-level transforms."""

from __future__ import annotations

import random
from dataclasses import dataclass
from enum import Enum
from typing import Any, Literal

from app.engine.melody.rhythm_cell import intervals_to_adjacent_steps


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


def _as_pitch_intervals(seq: list[int]) -> list[int]:
    """Normalize a pitch list to cumulative intervals from the head."""
    if not seq:
        return seq
    if max(abs(x) for x in seq) <= 24:
        return list(seq)
    head = seq[0]
    return [int(p) - int(head) for p in seq]


def pitch_cell_similarity(intervals_a: list[int], intervals_b: list[int]) -> float:
    """Return similarity in [0, 1] between two pitch-cell interval lists."""
    intervals_a = _as_pitch_intervals(intervals_a)
    intervals_b = _as_pitch_intervals(intervals_b)
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


def apply_pitch_technique(
    intervals: list[int],
    technique: DevelopmentTechnique,
    rng: random.Random,
    *,
    alternate_intervals: list[int] | None = None,
    sequence_semitones: int = 2,
) -> list[int]:
    """Transform pitch-cell interval DNA for a development technique."""
    ivs = list(intervals)
    if not ivs:
        return ivs

    if technique == DevelopmentTechnique.LITERAL:
        return ivs
    if technique == DevelopmentTechnique.SEQUENCE:
        return [iv + sequence_semitones for iv in ivs]
    if technique == DevelopmentTechnique.PITCH_SWAP:
        if alternate_intervals:
            return list(alternate_intervals)
        return [-iv for iv in ivs]
    if technique == DevelopmentTechnique.ORNAMENTATION:
        out: list[int] = []
        for iv in ivs:
            out.append(iv)
            if rng.random() < 0.35:
                out.append(iv + rng.choice([-1, 1, 2]))
        return out[: len(ivs) + 2]
    if technique == DevelopmentTechnique.FRAGMENTATION:
        return ivs[: max(2, len(ivs) // 2 + 1)]
    if technique == DevelopmentTechnique.EXTENSION and len(ivs) >= 2:
        tail = ivs[-1] + (ivs[-1] - ivs[-2])
        return ivs + [tail]
    return ivs


def apply_rhythm_to_motif(
    motif: dict[str, Any],
    technique: DevelopmentTechnique,
    *,
    alternate_motif: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return a shallow motif copy with rhythm_question/answer adjusted."""
    working = dict(motif)
    if technique != DevelopmentTechnique.RHYTHM_SWAP or alternate_motif is None:
        return working
    alt_rq = alternate_motif.get("rhythm_question")
    if alt_rq:
        working["rhythm_question"] = list(alt_rq)
    alt_ra = alternate_motif.get("rhythm_answer")
    if alt_ra:
        working["rhythm_answer"] = list(alt_ra)
    return working


def prepare_phrase_motif_for_technique(
    motif: dict[str, Any],
    technique: DevelopmentTechnique,
    rng: random.Random,
    *,
    alternate_motif: dict[str, Any] | None = None,
    sequence_semitones: int = 2,
) -> tuple[dict[str, Any], Literal["prime", "invert", "answer", "sequence"], int]:
    """Select/transform motivic cell DNA before phrase emission."""
    working = dict(motif)
    transform_q: Literal["prime", "invert", "answer", "sequence"] = "prime"
    seq = 0

    if technique == DevelopmentTechnique.PITCH_SWAP:
        own_ivs = list(working.get("intervals") or [])
        if alternate_motif is not None:
            alt_ivs = list(alternate_motif.get("intervals") or [])
            if tuple(own_ivs) != tuple(alt_ivs):
                ivs = [-iv for iv in own_ivs]
            else:
                working = dict(alternate_motif)
                ivs = alt_ivs
        else:
            ivs = [-iv for iv in own_ivs]
        working["intervals"] = ivs
        working["steps"] = intervals_to_adjacent_steps(ivs)
        return working, "prime", 0

    if technique == DevelopmentTechnique.SEQUENCE:
        return working, "sequence", sequence_semitones

    if technique == DevelopmentTechnique.LITERAL:
        return working, "prime", 0

    if technique == DevelopmentTechnique.RHYTHM_SWAP:
        working = apply_rhythm_to_motif(working, technique, alternate_motif=alternate_motif)
        return working, "prime", 0

    if technique in (
        DevelopmentTechnique.ORNAMENTATION,
        DevelopmentTechnique.FRAGMENTATION,
        DevelopmentTechnique.EXTENSION,
    ):
        alt_ivs = list((alternate_motif or {}).get("intervals") or [])
        ivs = apply_pitch_technique(
            list(working.get("intervals") or []),
            technique,
            rng,
            alternate_intervals=alt_ivs or None,
        )
        working["intervals"] = ivs
        working["steps"] = intervals_to_adjacent_steps(ivs)
        return working, "prime", 0

    return working, "prime", 0


def motif_plan_to_dict(plan: MotifPlan) -> dict[str, Any]:
    """JSON-serializable motif development plan."""
    return {
        "cell_id": plan.cell_id,
        "first_appearance": plan.first_appearance,
        "payoff_bar": plan.payoff_bar,
        "payoff_technique": plan.payoff_technique.value,
        "developments": [
            {"bar": bar, "technique": tech.value}
            for bar, tech in plan.developments
        ],
    }
