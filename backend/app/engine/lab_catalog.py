"""Compose Lab options — user-facing compressed parameters."""

from __future__ import annotations

from typing import Any

from app.engine.catalog import DANCE_TYPES, FORMS
from app.engine.generation_options import DEFAULTS
from app.engine.intent import intent_tag_catalog

ARCHETYPES: dict[str, dict[str, Any]] = {
    "segment_song": {
        "id": "segment_song",
        "form_id": "segment_song",
        "bars": 24,
        "label": {"en": "Segment (24 bars)", "zh": "片段（24 小節）"},
    },
    "classic_dance": {
        "id": "classic_dance",
        "form_id": "golden_age_short",
        "bars": 60,
        "label": {"en": "Extended arc (~60 bars)", "zh": "延伸曲式（約 60 小節）"},
    },
}

PROGRESSION_CHARACTERS: dict[str, dict[str, str]] = {
    "diatonic": {"minor": "i-iv-V7-i", "major": "I-IV-V-I"},
    "descending": {"minor": "descending_fifths", "major": "descending_fifths"},
    "chromatic": {"minor": "chromatic_bass", "major": "I-vi-IV-V"},
    "lyrical": {"minor": "i-VI-III-V7", "major": "I-vi-IV-V"},
}

PROGRESSION_CHARACTER_LABELS: dict[str, dict[str, str]] = {
    "diatonic": {"en": "Diatonic", "zh": "順階"},
    "descending": {"en": "Descending fifths", "zh": "下行五度"},
    "chromatic": {"en": "Chromatic bass", "zh": "半音低音"},
    "lyrical": {"en": "Lyrical detour", "zh": "抒情繞路"},
}

ENSEMBLE_PRESETS: dict[str, dict[str, Any]] = {
    "solo_piano": {
        "id": "solo_piano",
        "label": {"en": "Solo piano", "zh": "鋼琴 solo"},
        "instruments": {
            "piano": True,
            "guitar": False,
            "strings": False,
            "bandoneon": False,
        },
        "default_style_id": "simple",
    },
    "solo_guitar": {
        "id": "solo_guitar",
        "label": {"en": "Solo guitar", "zh": "吉他 solo"},
        "instruments": {
            "piano": False,
            "guitar": True,
            "strings": False,
            "bandoneon": False,
        },
        "default_style_id": "simple",
    },
    "piano_violin": {
        "id": "piano_violin",
        "label": {"en": "Piano + violin", "zh": "鋼琴 + 小提琴"},
        "instruments": {
            "piano": True,
            "guitar": False,
            "strings": True,
            "bandoneon": False,
        },
        "default_style_id": "di_sarli",
    },
    "small_combo": {
        "id": "small_combo",
        "label": {"en": "Small combo", "zh": "小型編制"},
        "instruments": {
            "piano": True,
            "guitar": True,
            "strings": True,
            "bandoneon": True,
        },
        "default_style_id": "canaro",
    },
}


def resolve_progression_id(character: str | None, mode: str) -> str | None:
    if not character or character in ("", "random"):
        return None
    mapping = PROGRESSION_CHARACTERS.get(character)
    if not mapping:
        return None
    return mapping.get(mode) or mapping.get("minor")


def resolve_archetype_form_id(archetype_id: str | None) -> str | None:
    if not archetype_id or archetype_id in ("", "random"):
        return None
    spec = ARCHETYPES.get(archetype_id)
    return spec["form_id"] if spec else None


def lab_options(style_references: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    return {
        "dance_types": [{"id": k} for k in DANCE_TYPES],
        "modes": [
            {"id": "random", "label": {"en": "Random", "zh": "隨機"}},
            {"id": "major", "label": {"en": "Major", "zh": "大調"}},
            {"id": "minor", "label": {"en": "Minor", "zh": "小調"}},
        ],
        "progression_characters": [
            {"id": k, "label": PROGRESSION_CHARACTER_LABELS[k]}
            for k in PROGRESSION_CHARACTERS
        ],
        "archetypes": list(ARCHETYPES.values()),
        "forms": [{"id": k} for k in FORMS],
        "intent_tags": intent_tag_catalog(),
        "ensemble_presets": list(ENSEMBLE_PRESETS.values()),
        "generation_options_defaults": DEFAULTS,
        "style_references": style_references or [],
        "segment_bars_default": 24,
    }
