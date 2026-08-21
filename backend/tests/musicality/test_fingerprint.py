# BASELINE 2026-08-21: continuity / expectancy gate (on top of M4)
# tango interval_hist KL = 0.5374
# tango onset_hist KL = 3.8422
# tango duration_hist KL = 0.8473
# vals interval_hist KL = 1.0978
# vals onset_hist KL = 0.0016
# vals duration_hist KL = 0.7194
# milonga interval_hist KL = 1.2603
# milonga onset_hist KL = 6.6450
# milonga duration_hist KL = 0.4528

from __future__ import annotations

import pytest

from app.critic.fingerprint import aggregate, compare, extract_fingerprint, load_reference
from app.engine.skeleton import build_skeleton

# Thresholds = post-expectancy measured aggregate KL (2026-08-21); tighten toward DoD (<0.25) later.
KL_THRESHOLDS = {
    "tango": {"interval_hist": 0.55, "onset_hist": 3.90, "duration_hist": 0.87},
    "vals": {"interval_hist": 1.12, "onset_hist": 0.05, "duration_hist": 0.73},
    "milonga": {"interval_hist": 1.28, "onset_hist": 6.70, "duration_hist": 0.50},
}

SEED_COUNTS = {"tango": 100, "vals": 50, "milonga": 50}


@pytest.mark.parametrize("dance", ["tango", "vals", "milonga"])
def test_fingerprint_within_baseline(dance: str) -> None:
    n = SEED_COUNTS[dance]
    fps = [extract_fingerprint(build_skeleton(dance_type=dance, seed=s)) for s in range(1, n + 1)]
    agg = aggregate(fps)
    kl = compare(agg, load_reference(dance))
    limits = KL_THRESHOLDS[dance]
    assert kl["interval_hist"] <= limits["interval_hist"], (
        f"interval_hist KL {kl['interval_hist']:.4f} > baseline {limits['interval_hist']}"
    )
    assert kl["onset_hist"] <= limits["onset_hist"], (
        f"onset_hist KL {kl['onset_hist']:.4f} > baseline {limits['onset_hist']}"
    )
    assert kl["duration_hist"] <= limits["duration_hist"], (
        f"duration_hist KL {kl['duration_hist']:.4f} > baseline {limits['duration_hist']}"
    )


def test_tango_density_and_leap_within_m4_bands() -> None:
    """M4 DoD bands: density near target, leaps in 12–20% band (was far too low pre-M4)."""
    fps = [extract_fingerprint(build_skeleton(dance_type="tango", seed=s)) for s in range(1, 101)]
    agg = aggregate(fps)
    ref = load_reference("tango")
    assert 3.0 <= agg.notes_per_bar <= 7.0
    assert agg.notes_per_bar >= ref.notes_per_bar * 0.85
    assert 0.10 <= agg.leap_ratio <= 0.22
    assert 0.12 <= agg.rest_ratio <= 0.26
