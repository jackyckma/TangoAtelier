from __future__ import annotations

import random

from app.engine.harmony_vocab import (
    UnknownChordSymbol,
    apply_inversion,
    chord_spec,
    normalize_symbol,
)

# Scales still used by melody / contour (not chord spelling).
MINOR_SCALE = (0, 2, 3, 5, 7, 8, 10)
HARMONIC_MINOR = (0, 2, 3, 5, 7, 8, 11)
MAJOR_SCALE = (0, 2, 4, 5, 7, 9, 11)

TONICS = {
    "A": 57,
    "D": 50,
    "E": 52,
    "G": 55,
    "C": 48,
    "F": 53,
    "Bb": 58,
    "Eb": 51,
}

_PC_LETTER = {
    0: "C",
    2: "D",
    3: "Eb",
    4: "E",
    5: "F",
    7: "G",
    9: "A",
    10: "Bb",
}

PROGRESSIONS_MINOR = {
    "i-iv-V7-i": ["i", "iv", "V7", "i"],
    "i-iv-V7b9-i": ["i", "iv", "V7b9", "i"],
    "i-VI-III-V7": ["i", "VI", "III", "V7"],
    "descending_fifths": ["i", "iv", "bVII", "III", "VI", "iiø7", "V7", "i"],
    "borrowed_chords": ["i", "iv", "V7", "VI", "iii", "V7", "i"],
    "tritone_substitution_flavour": ["i", "iv", "V7", "i"],
    "chromatic_bass": ["i", "iM7", "i7", "i6", "iv", "V7", "i", "i"],
    "neapolitan_cadence": ["i", "iv", "bII", "V7", "i"],
    "secondary_dominant": ["i", "V7/iv", "iv", "V7/V", "V7", "i"],
    "picardy_close": ["i", "iv", "V7b9", "i", "iv", "V7", "I"],
}

PROGRESSIONS_MAJOR = {
    "I-IV-V-I": ["I", "IV", "V", "I"],
    "I-vi-IV-V": ["I", "vi", "IV", "V"],
    "descending_fifths": ["I", "IV", "vii°", "iii", "vi", "ii", "V7", "I"],
}


def chord_pitches(
    tonic: int,
    mode: str,
    symbol: str,
    *,
    inversion: int = 0,
    octave_shift: int = 0,
) -> list[int]:
    spec = chord_spec(symbol, mode)
    root = tonic + spec.root_semitones + octave_shift * 12
    pitches = [root + iv for iv in spec.intervals]
    return apply_inversion(pitches, inversion)


def pick_progression(rng: random.Random, profile: dict, mode: str) -> list[str]:
    tendencies = profile.get("harmonic_tendencies", {})
    names = tendencies.get("typical_progressions") or []
    table = PROGRESSIONS_MINOR if mode == "minor" else PROGRESSIONS_MAJOR
    for name in names:
        if name in table:
            return list(table[name])
    return list(next(iter(table.values())))


def build_chord_plan(
    rng: random.Random,
    profile: dict,
    mode: str,
    total_bars: int,
    bars_per_chord: int = 2,
) -> list[tuple[int, str]]:
    progression = pick_progression(rng, profile, mode)
    plan: list[tuple[int, str]] = []
    i = 0
    while len(plan) * bars_per_chord < total_bars:
        plan.append((len(plan) * bars_per_chord, progression[i % len(progression)]))
        i += 1
    return plan


def pick_key(rng: random.Random, profile: dict) -> tuple[str, str, int]:
    mode_pref = profile.get("harmonic_tendencies", {}).get("primary_mode", "harmonic_minor")
    if mode_pref == "major_or_harmonic_minor":
        mode = rng.choice(["minor", "major"])
    elif mode_pref == "major":
        mode = "major"
    else:
        mode = "minor"
    name = rng.choice(list(TONICS.keys()))
    tonic = TONICS[name]
    key_name = f"{name} {'minor' if mode == 'minor' else 'major'}"
    return key_name, mode, tonic


def relative_key(key_name: str, mode: str, tonic: int) -> tuple[str, str, int] | None:
    """Relative major/minor (A minor ↔ C major). Returns None if spelling unsupported."""
    if mode == "minor":
        rel_tonic = tonic + 3
        rel_mode = "major"
    else:
        rel_tonic = tonic - 3
        rel_mode = "minor"
    letter = _PC_LETTER.get(rel_tonic % 12)
    if letter is None or letter not in TONICS:
        return None
    catalog = TONICS[letter]
    while catalog % 12 != rel_tonic % 12:
        catalog += 1
    while catalog - tonic > 6:
        catalog -= 12
    while tonic - catalog > 6:
        catalog += 12
    return f"{letter} {rel_mode}", rel_mode, catalog


__all__ = [
    "HARMONIC_MINOR",
    "MAJOR_SCALE",
    "MINOR_SCALE",
    "PROGRESSIONS_MAJOR",
    "PROGRESSIONS_MINOR",
    "TONICS",
    "UnknownChordSymbol",
    "chord_pitches",
    "normalize_symbol",
    "pick_key",
    "pick_progression",
    "relative_key",
]
