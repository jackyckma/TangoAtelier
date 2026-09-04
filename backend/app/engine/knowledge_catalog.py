"""Research hypothesis loader for optional catalog-backed Lab selection."""

from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.engine.harmony import PROGRESSIONS_MAJOR, PROGRESSIONS_MINOR

_HYPOTHESES_DIR = (
    Path(__file__).resolve().parents[3] / "docs" / "research" / "knowledge" / "hypotheses"
)

_KNOWN_TEMPLATE_IDS = frozenset(PROGRESSIONS_MINOR) | frozenset(PROGRESSIONS_MAJOR)

_CHARACTER_RE = re.compile(r"progression_character=(\w+)")


@lru_cache(maxsize=1)
def _load_all_hypotheses() -> tuple[dict[str, Any], ...]:
    if not _HYPOTHESES_DIR.is_dir():
        return ()
    loaded: list[dict[str, Any]] = []
    for path in sorted(_HYPOTHESES_DIR.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(data, dict) and data.get("id"):
            loaded.append(data)
    return tuple(loaded)


def catalog_selectable() -> bool:
    """True when at least 3 progression or sentence hypotheses are on disk."""
    hyps = _load_all_hypotheses()
    relevant = [h for h in hyps if h.get("kind") in ("progression", "sentence")]
    return len(relevant) >= 3


def _relevant_hypotheses() -> list[dict[str, Any]]:
    return [h for h in _load_all_hypotheses() if h.get("kind") in ("progression", "sentence")]


def templates_from_hint(engine_hint: str) -> list[str]:
    return [tid for tid in _KNOWN_TEMPLATE_IDS if tid in engine_hint]


def character_from_hint(engine_hint: str) -> str | None:
    match = _CHARACTER_RE.search(engine_hint or "")
    return match.group(1) if match else None


def catalog_progression_boost(
    character: str,
    mode: str,
    base_pool: list[str],
) -> tuple[list[str], list[str]]:
    """Return (augmented_pool, consulted_hypothesis_ids).

    Fails closed when the catalog is missing or has fewer than 3 relevant hypotheses.
    """
    if not catalog_selectable():
        return list(base_pool), []

    consulted_ids: list[str] = []
    extra: list[str] = []
    table = PROGRESSIONS_MINOR if mode == "minor" else PROGRESSIONS_MAJOR

    for hyp in _relevant_hypotheses():
        consulted_ids.append(str(hyp["id"]))
        if hyp.get("kind") != "progression":
            continue
        hint = str(hyp.get("engine_hint") or "")
        hinted_char = character_from_hint(hint)
        if hinted_char and hinted_char != character:
            continue
        for template_id in templates_from_hint(hint):
            if template_id in table and template_id not in extra:
                extra.append(template_id)

    if len(consulted_ids) < 3:
        return list(base_pool), []

    merged = list(base_pool)
    for template_id in extra:
        if template_id not in merged:
            merged.append(template_id)
    return merged, consulted_ids


def sentence_hints_from_catalog() -> list[dict[str, str]]:
    """Phrase-related hints from sentence hypotheses (empty when catalog unavailable)."""
    if not catalog_selectable():
        return []
    out: list[dict[str, str]] = []
    for hyp in _relevant_hypotheses():
        if hyp.get("kind") != "sentence":
            continue
        out.append(
            {
                "id": str(hyp["id"]),
                "engine_hint": str(hyp.get("engine_hint") or ""),
            }
        )
    return out
