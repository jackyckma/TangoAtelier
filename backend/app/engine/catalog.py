"""Shared, orchestra-independent options for the Atelier skeleton layer."""

from __future__ import annotations

# Dance fingerprints used by skeleton + simple render (teaching caricatures).
# - tango: 2/4, walking marcato feel, slower harmonic rhythm
# - milonga: 2/4, faster, habanera / 3+3+2 pulse, earthy & playful
# - vals: 3/4, bass–chord–chord on 1–2–3, flowing / circular, lyric melody
DANCE_TYPES = {
    "tango": {
        "id": "tango",
        "time_signature": (2, 4),
        # Quarter-note BPM (marcato walking pace)
        "default_bpm": 64,
        "bars_per_chord": 2,
        "default_rhythm": "marcato_en_dos",
        "key_bias": "minor",
        "melody_feel": "cantabile",
    },
    "milonga": {
        "id": "milonga",
        "time_signature": (2, 4),
        # Faster than tango; still readable on Salamander piano
        "default_bpm": 104,
        # Quicker harmonic turnover matches milonga drive
        "bars_per_chord": 1,
        "default_rhythm": "milonga_habanera",
        "alt_rhythm": "milonga_332",
        "key_bias": "major",
        "melody_feel": "playful_syncopated",
    },
    "vals": {
        "id": "vals",
        "time_signature": (3, 4),
        # Quarter BPM ≈ 170–190 → one step-on-1 per ~1s bar (Argentine vals pace)
        "default_bpm": 176,
        "bars_per_chord": 2,
        "default_rhythm": "vals_bass_chord",
        "key_bias": "major",
        "melody_feel": "lyrical_waltz",
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

KEYS_MAJOR = [k for k in KEYS if k.endswith("major")]
KEYS_MINOR = [k for k in KEYS if k.endswith("minor")]


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
