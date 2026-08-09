"""Shared, orchestra-independent options for the Atelier skeleton layer."""

from __future__ import annotations

DANCE_TYPES = {
    "tango": {
        "id": "tango",
        "time_signature": (2, 4),
        "default_bpm": 64,
        "bars_per_chord": 2,
    },
    "milonga": {
        "id": "milonga",
        "time_signature": (2, 4),
        "default_bpm": 96,
        "bars_per_chord": 2,
    },
    "vals": {
        "id": "vals",
        "time_signature": (3, 4),
        "default_bpm": 66,
        "bars_per_chord": 2,
    },
}

# Form templates: list of (section_name, bars)
FORMS = {
    "intro_aa_coda": {
        "id": "intro_aa_coda",
        "sections": [("intro", 4), ("A", 16), ("A_prime", 16), ("coda", 4)],
    },
    "aaba": {
        "id": "aaba",
        "sections": [("A", 8), ("A", 8), ("B", 8), ("A", 8)],
    },
    "abab": {
        "id": "abab",
        "sections": [("A", 8), ("B", 8), ("A", 8), ("B", 8)],
    },
}

PROGRESSIONS_MINOR = {
    "i-iv-V7-i": ["i", "iv", "V7", "i"],
    "i-VI-III-V7": ["i", "VI", "III", "V7"],
    "descending_fifths": ["i", "iv", "VII", "III", "VI", "iiø", "V7", "i"],
}

PROGRESSIONS_MAJOR = {
    "I-IV-V-I": ["I", "IV", "V", "I"],
    "I-vi-IV-V": ["I", "vi", "IV", "V"],
    "descending_fifths": ["I", "IV", "vii°", "iii", "vi", "ii", "V7", "I"],
}

KEYS = [
    "A minor",
    "D minor",
    "E minor",
    "G minor",
    "C major",
    "F major",
    "G major",
    "D major",
]


def atelier_options() -> dict:
    return {
        "dance_types": [
            {"id": "tango"},
            {"id": "milonga"},
            {"id": "vals"},
        ],
        "keys": KEYS,
        "forms": [{"id": k} for k in FORMS],
        "progressions": {
            "minor": [{"id": k} for k in PROGRESSIONS_MINOR],
            "major": [{"id": k} for k in PROGRESSIONS_MAJOR],
        },
        "render_styles": [
            {"id": "simple", "personality_type": "neutral"},
        ],
    }
