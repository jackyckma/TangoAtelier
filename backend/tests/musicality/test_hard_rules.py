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


def test_critic_detects_chord_spelling_bug() -> None:
    """§1 bug 1: harmonic-minor VII spelling must be flagged when it appears."""
    found = False
    for seed in range(1, 201):
        sk = build_skeleton(dance_type="tango", seed=seed)
        if sk.get("progression_id") != "descending_fifths":
            continue
        rendered = render_skeleton(
            sk, SIMPLE_PROFILE, seed=sk["seed"], include_midi=False, include_musicxml=False
        )
        spelling = [
            v for v in check_hard_rules(sk, rendered) if v.rule_id == "CHORD_SPELLING_INVALID"
        ]
        if spelling:
            found = True
            break
    assert found, "CHORD_SPELLING_INVALID should fire on descending_fifths VII spelling"


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
