"""Continuity / expectancy gates (founder 2026-08-20).

Variance must serve the drama arc — not chop sentences mid-rise or spray
notes / chord colour when the emotion asks to stay stable.
"""

from __future__ import annotations

from typing import Literal

Level = Literal["low", "medium", "high"]

STABLE_TAGS = frozenset({"normal", "release", "pause"})
DRIVE_TAGS = frozenset({"rise", "anticipate", "climax", "dense"})


def is_stable(drama_tag: str) -> bool:
    return (drama_tag or "normal") in STABLE_TAGS


def is_drive(drama_tag: str) -> bool:
    return (drama_tag or "normal") in DRIVE_TAGS


def plan_rest_bars(
    phrase_bars: int,
    *,
    drama_tag: str = "normal",
    energy: float = 0.5,
    pause_frequency: str = "medium",
    rng_pick_last: bool = False,
) -> set[int]:
    """Choose phrase-relative bars that may leave ≥1 beat of melodic air.

    Rules (continuity):
    - Never rest on bar 0 (open the sentence).
    - On rise / anticipate / climax: only the final bar may breathe (after the goal).
    - On stable / release: prefer late answer bars (2nd half), not mid-question cuts.
    - pause drama or high pause_frequency: allow one extra late rest when stable.
    """
    rests: set[int] = set()
    if phrase_bars <= 0:
        return rests

    tag = drama_tag or "normal"
    if is_drive(tag) and tag != "dense":
        # Keep the line singing through the climb; breathe only after landing
        if phrase_bars >= 2:
            rests.add(phrase_bars - 1)
        return rests

    if phrase_bars == 1:
        return rests

    if phrase_bars >= 4:
        # After the answer — last bar of each 4-bar chunk, not the 2nd (mid-question)
        for chunk_start in range(0, phrase_bars, 4):
            chunk = min(4, phrase_bars - chunk_start)
            if chunk < 2:
                continue
            pick = chunk_start + chunk - 1
            if chunk >= 4 and rng_pick_last is False and energy < 0.45:
                # Slightly earlier only when calm — still in answer half
                pick = chunk_start + 2
            rests.add(pick)
    else:
        rests.add(phrase_bars - 1)

    if tag == "pause" or (pause_frequency == "high" and is_stable(tag) and phrase_bars >= 4):
        mid = phrase_bars // 2
        if mid > 0:
            rests.add(mid)

    rests.discard(0)
    return rests


def prefer_breath_cell(drama_tag: str, *, leave_rest: bool, material_count: int) -> bool:
    """Stable emotion → breath / long cells; drive may use denser cells."""
    if leave_rest:
        return True
    if is_stable(drama_tag):
        return True
    if drama_tag == "rise":
        return material_count <= 3
    return False


def allow_dense_rhythm_cell(drama_tag: str, density: str) -> bool:
    """Rapid note strings only when density+drama ask for drive."""
    if density == "low":
        return False
    if is_stable(drama_tag):
        return False
    if drama_tag == "rise" and density != "high":
        return False
    return drama_tag in ("climax", "dense", "anticipate") or (
        drama_tag == "rise" and density == "high"
    )


def development_level_cap(
    *,
    local_bar: int,
    section_bars: int,
    drama_tag: str,
    energy: float,
    section_name: str,
) -> int:
    """0–3 surface intensity — early/stable phrases stay near the cell, not fancy."""
    span = max(1, section_bars - 1)
    # Progress through the section, but start lower so A doesn't invent from bar 1
    level = int(round(2.2 * max(0, local_bar) / span))
    if is_stable(drama_tag) and energy < 0.6:
        level = min(level, 1)
    if drama_tag in ("dense", "climax"):
        level += 1
    elif drama_tag == "rise" and energy >= 0.55:
        level += 1
    if energy >= 0.8 and is_drive(drama_tag):
        level += 1
    if section_name == "A_prime" and is_drive(drama_tag):
        level += 1
    elif section_name == "A_prime" and is_stable(drama_tag):
        level = min(level + 1, 2)  # recap can bloom, not dump
    return max(0, min(3, level))


def density_for_drama(base: Level, tag: str, *, dance_type: str) -> Level:
    """Drama shapes intensity — never spray notes on stable emotion."""
    order: list[Level] = ["low", "medium", "high"]
    idx = order.index(base) if base in order else 1
    if tag in ("anticipate", "pause", "release"):
        return order[max(0, idx - 1)]
    if tag == "rise":
        return base
    if tag == "climax":
        if dance_type in ("vals", "milonga"):
            return base
        return order[min(2, idx + 1)]
    if tag == "dense":
        return base
    # normal / stable: never bump above base
    return base


def phrase_transform(
    *,
    section_name: str,
    phrase_i: int,
    drama_tag: str,
    energy: float,
    seq_unit: int,
) -> tuple[Literal["prime", "invert", "answer", "sequence"], int]:
    """Motivic surface change only when the arc asks — else stay literal/prime."""
    if section_name == "B":
        if is_stable(drama_tag) and energy < 0.55 and phrase_i == 0:
            return "prime", 0
        if is_drive(drama_tag) or energy >= 0.55:
            if phrase_i % 2 == 1 and energy >= 0.65:
                return "invert", 0
            return "sequence", seq_unit * (1 + phrase_i // 2)
        # Mild B contrast without invert flip-flops
        return "sequence", seq_unit if phrase_i >= 1 else 0

    if section_name == "A_prime":
        if is_stable(drama_tag) and phrase_i == 0:
            return "prime", 0
        return "prime", seq_unit if phrase_i >= 2 and is_drive(drama_tag) else 0

    # A and others: stay on the cell; light sequence only late + drive
    if phrase_i >= 3 and is_drive(drama_tag):
        return "sequence", seq_unit
    return "prime", 0


def decoration_scale(drama: str, energy: float) -> float:
    """Ornament probability multiplier — quiet when stable."""
    base = {
        "climax": 1.35,
        "anticipate": 1.05,
        "rise": 1.05,
        "dense": 1.15,
        "pause": 0.35,
        "release": 0.55,
        "normal": 0.7,
    }.get(drama or "normal", 0.7)
    return base * (0.7 + 0.45 * float(energy))


def allow_deceptive_cadence(
    *,
    section_name: str,
    phrase_index: int,
    n_phrases: int,
    energy_hint: float = 0.5,
) -> bool:
    """Deceptive is a dramatic device — not a default mid-section colour trick."""
    if section_name in ("intro", "bridge", "coda"):
        return False
    if section_name == "A" and phrase_index < n_phrases - 1:
        return False  # keep A progressing toward authentic/half
    if section_name == "A_prime":
        # Only late, and only when we want a twist before final settle
        return phrase_index == n_phrases - 2 and n_phrases >= 3 and energy_hint >= 0.55
    if section_name == "B":
        return phrase_index == n_phrases - 2 and n_phrases >= 3
    return False


def harmonic_rhythm_hold(
    local_bar: int,
    phrase_bars: int,
    *,
    drama_tag: str = "normal",
    section_name: str = "A",
) -> int:
    """0 = hold previous chord; 1 = new chord.

    Stable emotion → longer holds (serve the line). Drive / cadence zone → move.
    """
    if local_bar >= phrase_bars - 1:
        return 1
    if local_bar >= phrase_bars - 2:
        return 1
    if is_stable(drama_tag) or section_name in ("A", "A_prime"):
        # Hold 2 bars at a time in the body
        return 1 if local_bar % 2 == 0 else 0
    if section_name == "B" and is_drive(drama_tag):
        return 1  # more motion when B is driving
    return 1 if local_bar % 2 == 1 else 0
