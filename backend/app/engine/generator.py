"""Backward-compatible one-shot generate = skeleton + orchestra render."""

from __future__ import annotations

from app.engine.render import SIMPLE_PROFILE, render_skeleton
from app.engine.skeleton import build_skeleton


def generate_piece(
    profile: dict,
    seed: int | None = None,
    *,
    include_musicxml: bool = False,
    include_midi: bool = True,
    dance_type: str = "tango",
) -> dict:
    skeleton = build_skeleton(dance_type=dance_type, seed=seed)
    return render_skeleton(
        skeleton,
        profile,
        seed=seed,
        include_midi=include_midi,
        include_musicxml=include_musicxml,
    )


def generate_simple_from_skeleton(skeleton: dict, **kwargs) -> dict:
    return render_skeleton(skeleton, SIMPLE_PROFILE, **kwargs)
