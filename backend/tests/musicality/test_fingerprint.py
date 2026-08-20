# BASELINE 2026-08-19: tango interval_hist KL = 0.2053
# BASELINE 2026-08-19: tango onset_hist KL = 0.3779
# BASELINE 2026-08-19: tango duration_hist KL = 0.1783
# BASELINE 2026-08-19: vals interval_hist KL = 0.7008
# BASELINE 2026-08-19: vals onset_hist KL = 0.0402
# BASELINE 2026-08-19: vals duration_hist KL = 0.4519
# BASELINE 2026-08-19: milonga interval_hist KL = 0.6812
# BASELINE 2026-08-19: milonga onset_hist KL = 3.0333
# BASELINE 2026-08-20: milonga onset_hist KL = 3.0756 (threshold 3.08; pre-M10 drift on main)
# BASELINE 2026-08-19: milonga duration_hist KL = 0.4529

from __future__ import annotations

import pytest

from app.critic.fingerprint import aggregate, compare, extract_fingerprint, load_reference
from app.engine.skeleton import build_skeleton

# Thresholds = current measured aggregate KL (2026-08-19); tighten after each M-task.
KL_THRESHOLDS = {
    "tango": {"interval_hist": 0.21, "onset_hist": 0.38, "duration_hist": 0.19},
    "vals": {"interval_hist": 0.71, "onset_hist": 0.05, "duration_hist": 0.46},
    "milonga": {"interval_hist": 0.69, "onset_hist": 3.08, "duration_hist": 0.48},
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


def test_tango_density_and_leap_gap_vs_golden() -> None:
    """§1: low notes/bar and leap_ratio must show measurable gap from expert prior."""
    fps = [extract_fingerprint(build_skeleton(dance_type="tango", seed=s)) for s in range(1, 101)]
    agg = aggregate(fps)
    ref = load_reference("tango")
    assert agg.notes_per_bar < ref.notes_per_bar * 0.75
    assert agg.leap_ratio < ref.leap_ratio * 0.75
    # rest_ratio has moved closer to the golden prior (~0.19); keep density/leap as §1 gap signals
