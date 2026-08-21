"""Continuity / expectancy gate tests (founder 2026-08-20)."""

from __future__ import annotations

from collections import Counter

from app.engine.form import plan_phrases
from app.engine.melody.expectancy import (
    allow_dense_rhythm_cell,
    allow_deceptive_cadence,
    plan_rest_bars,
    phrase_transform,
)
from app.engine.melody.connect import plan_rests
from app.engine.skeleton import build_skeleton
import random


def test_rise_rests_only_at_phrase_end() -> None:
    rests = plan_rest_bars(4, drama_tag="rise", energy=0.7)
    assert rests == {3}
    assert 0 not in rests
    assert 1 not in rests


def test_stable_rests_not_on_downbeat_open() -> None:
    rests = plan_rest_bars(4, drama_tag="normal", energy=0.4, rng_pick_last=True)
    assert 0 not in rests
    assert max(rests) >= 2


def test_dense_cells_blocked_when_stable() -> None:
    assert allow_dense_rhythm_cell("normal", "high") is False
    assert allow_dense_rhythm_cell("climax", "high") is True
    assert allow_dense_rhythm_cell("rise", "medium") is False


def test_b_transform_stays_prime_when_calm() -> None:
    t, seq = phrase_transform(
        section_name="B", phrase_i=0, drama_tag="normal", energy=0.4, seq_unit=2
    )
    assert t == "prime"
    assert seq == 0


def test_a_section_avoids_default_deceptive() -> None:
    rng = random.Random(1)
    phrases = plan_phrases(
        section_name="A",
        bars=16,
        dance_type="tango",
        bar_from_1based=5,
        pause_bars=set(),
        rng=rng,
    )
    cads = [p.cadence for p in phrases]
    assert "deceptive" not in cads


def test_deceptive_policy_late_only() -> None:
    assert allow_deceptive_cadence(
        section_name="A", phrase_index=1, n_phrases=4, energy_hint=0.9
    ) is False
    assert allow_deceptive_cadence(
        section_name="A_prime", phrase_index=2, n_phrases=4, energy_hint=0.6
    ) is True


def test_skeleton_phrase_continuity_no_mid_rise_chop() -> None:
    """On rise bars, plan_rests must not cut the opening of the phrase."""
    for seed in range(1, 21):
        rests = plan_rests(4, random.Random(seed), drama_tag="rise", energy=0.75)
        assert 0 not in rests
        assert rests <= {3}


def test_b_keeps_progression_family_under_relative_mod() -> None:
    sk = build_skeleton(
        dance_type="tango",
        seed=7,
        progression_id="descending_fifths",
        form_id="golden_age_short",
    )
    home = sk["progression_id"]
    b = next(s for s in sk["harmony_plan"] if s["section"] == "B")
    assert b["progression_id"] == home
    assert str(b.get("modulation") or "").startswith("relative")


def test_unique_chord_rate_not_exploding_in_a() -> None:
    """A section should mostly cycle the progression — not a new colour every bar."""
    sk = build_skeleton(dance_type="tango", seed=3, form_id="golden_age_short")
    a_chords = [c["symbol"] for c in sk["chords"] if c.get("section") == "A"]
    # With 2-bar holds, unique count should be well below bar count
    assert len(set(a_chords)) <= max(6, len(a_chords) // 2 + 2)
