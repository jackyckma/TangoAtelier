"""Compose Lab orchestration — skeleton build, extend, render params."""

from __future__ import annotations

from typing import Any, Literal

from app.engine.generation_options import normalize_generation_options
from app.engine.intent import merge_intent_tags
from app.engine.lab_catalog import (
    ENSEMBLE_PRESETS,
    resolve_archetype_form_id,
    resolve_progression_id,
)
from app.engine.skeleton import build_skeleton

MelodyLevel = Literal["low", "medium", "high"]


def build_lab_skeleton(
    *,
    dance_type: str = "tango",
    mode: str | None = "minor",
    progression_character: str | None = "diatonic",
    archetype_id: str | None = "segment_song",
    melody_density: MelodyLevel = "medium",
    melody_variation: MelodyLevel = "medium",
    intent_tags: list[str] | None = None,
    generation_options: dict[str, Any] | None = None,
    seed: int | None = None,
    key: str | None = None,
    progression_id: str | None = None,
    form_id: str | None = None,
) -> dict[str, Any]:
    tag_params, translation = merge_intent_tags(intent_tags)
    opts = normalize_generation_options(
        {**(generation_options or {}), **(tag_params.pop("generation_options", {}) or {})}
    )

    dance_type = str(tag_params.get("dance_type") or dance_type)
    mode = str(tag_params.get("mode") or mode or "minor")
    progression_character = str(
        tag_params.get("progression_character") or progression_character or "diatonic"
    )
    archetype_id = str(tag_params.get("archetype_id") or archetype_id or "segment_song")
    melody_density = tag_params.get("melody_density") or melody_density
    melody_variation = tag_params.get("melody_variation") or melody_variation

    resolved_form = form_id or resolve_archetype_form_id(archetype_id) or "segment_song"
    resolved_prog = progression_id or resolve_progression_id(
        None if progression_character == "random" else progression_character,
        "minor" if mode == "random" else mode,
    )

    sk = build_skeleton(
        dance_type=dance_type,
        key=key if key else (mode if mode in ("major", "minor") else None),
        progression_id=resolved_prog or "random",
        form_id=resolved_form,
        melody_density=melody_density,
        melody_variation=melody_variation,
        seed=seed,
        generation_options=opts,
    )
    sk["generation_options"] = opts
    sk["archetype_id"] = archetype_id
    sk["progression_character"] = progression_character
    sk["segment_bars"] = sk.get("bars")
    sk["intent_translation"] = translation
    if tag_params.get("style_id"):
        sk["suggested_style_id"] = tag_params["style_id"]
    if tag_params.get("ensemble_id"):
        sk["suggested_ensemble_id"] = tag_params["ensemble_id"]
    return sk


def extend_lab_skeleton(
    *,
    seed: int,
    dance_type: str = "tango",
    mode: str | None = "minor",
    progression_character: str | None = "diatonic",
    melody_density: MelodyLevel = "medium",
    melody_variation: MelodyLevel = "medium",
    generation_options: dict[str, Any] | None = None,
    intent_tags: list[str] | None = None,
) -> dict[str, Any]:
    return build_lab_skeleton(
        dance_type=dance_type,
        mode=mode,
        progression_character=progression_character,
        archetype_id="classic_dance",
        melody_density=melody_density,
        melody_variation=melody_variation,
        intent_tags=intent_tags,
        generation_options=generation_options,
        seed=seed,
    )


def resolve_ensemble(ensemble_id: str | None) -> dict[str, Any]:
    eid = ensemble_id or "solo_piano"
    preset = ENSEMBLE_PRESETS.get(eid) or ENSEMBLE_PRESETS["solo_piano"]
    return preset
