"""M6: skeleton exports motif_development_plans (T-0016 acceptance)."""

from __future__ import annotations

import json

from app.engine.skeleton import build_skeleton


def test_motif_development_plans_export_contract() -> None:
    sk = build_skeleton(seed=42, dance_type="tango")
    plans = sk.get("motif_development_plans") or []
    assert plans

    first = plans[0]
    assert "cell_id" in first
    assert "first_appearance" in first
    assert "payoff_bar" in first
    assert "payoff_technique" in first
    assert "developments" in first
    assert isinstance(first["payoff_technique"], str)
    assert first["payoff_bar"] > first["first_appearance"]

    for dev in first["developments"]:
        assert "bar" in dev
        assert "technique" in dev
        assert isinstance(dev["technique"], str)

    json.dumps(plans)


def test_motif_development_plans_reproducible() -> None:
    a = build_skeleton(seed=42, dance_type="tango")["motif_development_plans"]
    b = build_skeleton(seed=42, dance_type="tango")["motif_development_plans"]
    assert a == b
