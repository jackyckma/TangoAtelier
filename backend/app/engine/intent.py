"""Intent tag → parameter bundles for Compose Lab."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.engine.generation_options import normalize_generation_options

_BUNDLES_PATH = Path(__file__).resolve().parents[2] / "data" / "intent_bundles.json"


def _load_bundles() -> dict[str, Any]:
    with _BUNDLES_PATH.open(encoding="utf-8") as f:
        return json.load(f)


def intent_tag_catalog() -> list[dict[str, Any]]:
    data = _load_bundles()
    tags = data.get("tags") or {}
    out: list[dict[str, Any]] = []
    for tag_id, spec in tags.items():
        label = spec.get("label") or {}
        out.append(
            {
                "id": tag_id,
                "label_en": label.get("en") or tag_id,
                "label_zh": label.get("zh") or tag_id,
                "category": spec.get("category") or "mood",
            }
        )
    out.sort(key=lambda x: (x["category"], x["id"]))
    return out


def merge_intent_tags(tag_ids: list[str] | None) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Merge selected tags into skeleton/render params + human translation lines."""
    if not tag_ids:
        return {}, []

    data = _load_bundles()
    catalog = data.get("tags") or {}
    merged: dict[str, Any] = {}
    gen_opts: dict[str, Any] = {}
    translation: list[dict[str, Any]] = []

    for tid in tag_ids:
        spec = catalog.get(tid)
        if not spec:
            continue
        weights = spec.get("weights") or {}
        label = spec.get("label") or {}
        for key, val in weights.items():
            if key == "generation_options" and isinstance(val, dict):
                gen_opts.update(val)
            else:
                merged[key] = val
        translation.append(
            {
                "tag_id": tid,
                "label_en": label.get("en") or tid,
                "label_zh": label.get("zh") or tid,
                "applied": {k: v for k, v in weights.items() if k != "generation_options"},
            }
        )

    if gen_opts:
        merged["generation_options"] = normalize_generation_options(
            {**merged.get("generation_options", {}), **gen_opts}
        )
    return merged, translation
