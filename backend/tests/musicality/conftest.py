"""Shared fixtures for musicality tests."""

from __future__ import annotations

import pytest

from app.engine import SIMPLE_PROFILE, render_skeleton
from app.engine.skeleton import build_skeleton


@pytest.fixture
def render_simple():
    def _render(skeleton: dict):
        return render_skeleton(
            skeleton,
            SIMPLE_PROFILE,
            seed=int(skeleton["seed"]),
            include_midi=False,
            include_musicxml=False,
        )

    return _render


@pytest.fixture
def build_sk():
    return build_skeleton
