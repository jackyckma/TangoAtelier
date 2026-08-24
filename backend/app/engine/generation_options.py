"""Normalized generation_options for Compose Lab experiments."""

from __future__ import annotations

from typing import Any, Literal

SurfaceReharm = Literal["off", "low", "on"]
MotivicCells = Literal["single", "multi"]
YeitesIntensity = Literal["low", "medium", "high"]
HarmonicGrammar = Literal["legacy_templates", "functional"]

DEFAULTS: dict[str, Any] = {
    "expectancy_gate": True,
    "surface_reharm": "off",
    "motivic_cells": "multi",
    "phrase_transform_aggressive": False,
    "b_groove_contrast_run": True,
    "yeites_intensity": "medium",
    "a_prime_elaboration": True,
    "harmonic_grammar": "legacy_templates",
}


def normalize_generation_options(raw: dict[str, Any] | None) -> dict[str, Any]:
    out = dict(DEFAULTS)
    if not raw:
        return out
    for key in DEFAULTS:
        if key in raw and raw[key] is not None:
            out[key] = raw[key]
    if out["surface_reharm"] not in ("off", "low", "on"):
        out["surface_reharm"] = "off"
    if out["motivic_cells"] not in ("single", "multi"):
        out["motivic_cells"] = "multi"
    if out["yeites_intensity"] not in ("low", "medium", "high"):
        out["yeites_intensity"] = "medium"
    if out["harmonic_grammar"] not in ("legacy_templates", "functional"):
        out["harmonic_grammar"] = "legacy_templates"
    return out


def yeites_multiplier(intensity: str) -> float:
    return {"low": 0.45, "medium": 1.0, "high": 1.35}.get(intensity, 1.0)
