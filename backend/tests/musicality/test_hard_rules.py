# BASELINE 2026-08-19: tango error violations present on all 50 seeds (DENSITY_MISMATCH, etc.)
# Fingerprint KL baselines recorded in test_fingerprint.py

from __future__ import annotations

import pytest

from app.critic.rules import check_hard_rules, format_violations
from app.engine import SIMPLE_PROFILE, render_skeleton
from app.engine.skeleton import build_skeleton


@pytest.mark.parametrize("dance", ["tango", "vals", "milonga"])
@pytest.mark.parametrize("seed", range(1, 51))
def test_no_error_violations(dance: str, seed: int) -> None:
    sk = build_skeleton(dance_type=dance, seed=seed)
    rendered = render_skeleton(
        sk, SIMPLE_PROFILE, seed=sk["seed"], include_midi=False, include_musicxml=False
    )
    errors = [v for v in check_hard_rules(sk, rendered) if v.severity == "error"]
    assert not errors, format_violations(errors)


def test_descending_fifths_spells_bvii_correctly() -> None:
    """§1 bug 1 fixed: bVII in A minor = G–B–D pitch classes."""
    from app.engine.harmony import chord_pitches

    for seed in range(1, 201):
        sk = build_skeleton(
            dance_type="tango",
            seed=seed,
            progression_id="descending_fifths",
        )
        if sk.get("progression_id") != "descending_fifths":
            continue
        assert "bVII" in sk.get("progression") or "bVII" in str(sk.get("chords"))
        pcs = frozenset(p % 12 for p in chord_pitches(57, "minor", "bVII"))
        assert pcs == frozenset({7, 11, 2}), f"bVII PCs {pcs}"
        rendered = render_skeleton(
            sk, SIMPLE_PROFILE, seed=sk["seed"], include_midi=False, include_musicxml=False
        )
        spelling = [
            v for v in check_hard_rules(sk, rendered) if v.rule_id == "CHORD_SPELLING_INVALID"
        ]
        assert not spelling, format_violations(spelling)
        break
    else:
        raise AssertionError("No descending_fifths skeleton in 200 seeds")


def test_no_chord_spelling_violations_tango_sample() -> None:
    """M1 DoD: CHORD_SPELLING_INVALID should be zero on a tango seed batch."""
    from collections import Counter

    counts: Counter[str] = Counter()
    for seed in range(1, 101):
        sk = build_skeleton(dance_type="tango", seed=seed)
        rendered = render_skeleton(
            sk, SIMPLE_PROFILE, seed=sk["seed"], include_midi=False, include_musicxml=False
        )
        for v in check_hard_rules(sk, rendered):
            if v.rule_id == "CHORD_SPELLING_INVALID":
                counts[v.rule_id] += 1
    assert counts["CHORD_SPELLING_INVALID"] == 0


def test_musicxml_includes_harmony() -> None:
    sk = build_skeleton(dance_type="tango", seed=7, progression_id="descending_fifths")
    out = render_skeleton(
        sk, SIMPLE_PROFILE, seed=sk["seed"], include_midi=False, include_musicxml=True
    )
    xml = out.get("musicxml") or ""
    assert "<harmony" in xml
    assert len(xml) > 500


def test_iio7_has_seventh() -> None:
    """§1 bug 2 fixed: iiø7 includes the 7th (A in A minor)."""
    from app.engine.harmony import chord_pitches

    pcs = frozenset(p % 12 for p in chord_pitches(57, "minor", "iiø7"))
    assert pcs == frozenset({11, 2, 5, 9}), f"iiø7 PCs {pcs}"


def test_critic_detects_harmonic_rhythm_orphan() -> None:
    """§1 bug 3: 12-bar A section vs 8-bar harmonic cycle."""
    sk = build_skeleton(dance_type="tango", seed=7, form_id="intro_aa_coda")
    rendered = render_skeleton(
        sk, SIMPLE_PROFILE, seed=sk["seed"], include_midi=False, include_musicxml=False
    )
    orphans = [
        v for v in check_hard_rules(sk, rendered) if v.rule_id == "HARMONIC_RHYTHM_ORPHAN"
    ]
    assert orphans, "A-section length mismatch should trigger HARMONIC_RHYTHM_ORPHAN"
