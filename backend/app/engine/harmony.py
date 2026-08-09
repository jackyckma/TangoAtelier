from __future__ import annotations

import random

# Interval sets from chord root (semitones)
TRIAD_MIN = (0, 3, 7)
TRIAD_MAJ = (0, 4, 7)
TRIAD_DIM = (0, 3, 6)
DOM7 = (0, 4, 7, 10)

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

# pitch class → preferred spelling for relatives we generate
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
    "i-iv-V7b9-i": ["i", "iv", "V7", "i"],
    "descending_fifths": ["i", "iv", "VII", "III", "VI", "iiø", "V7", "i"],
    "i-VI-III-V7": ["i", "VI", "III", "V7"],
    "borrowed_chords": ["i", "iv", "V7", "VI", "iii", "V7", "i"],
    "tritone_substitution_flavour": ["i", "iv", "V7", "i"],
}

PROGRESSIONS_MAJOR = {
    "I-IV-V-I": ["I", "IV", "V", "I"],
    "descending_fifths": ["I", "IV", "vii°", "iii", "vi", "ii", "V7", "I"],
}


def _scale(mode: str) -> tuple[int, ...]:
    return HARMONIC_MINOR if mode == "minor" else MAJOR_SCALE


def _root_for_degree(tonic: int, mode: str, degree: int) -> int:
    scale = _scale(mode)
    return tonic + scale[(degree - 1) % 7]


def _quality_for(symbol: str, mode: str) -> tuple[int, ...]:
    if symbol in ("V7", "V7b9", "V"):
        return DOM7 if "7" in symbol else TRIAD_MAJ
    if symbol in ("i", "iv", "vi", "ii", "iii"):
        return TRIAD_MIN
    if symbol in ("I", "IV", "VI", "III", "VII"):
        return TRIAD_MAJ
    if symbol in ("iiø", "vii°"):
        return TRIAD_DIM
    return TRIAD_MIN if mode == "minor" else TRIAD_MAJ


def _degree_for(symbol: str) -> int:
    table = {
        "i": 1,
        "I": 1,
        "ii": 2,
        "iiø": 2,
        "iii": 3,
        "III": 3,
        "iv": 4,
        "IV": 4,
        "V": 5,
        "V7": 5,
        "V7b9": 5,
        "vi": 6,
        "VI": 6,
        "VII": 7,
        "vii°": 7,
    }
    return table.get(symbol, 1)


def chord_pitches(tonic: int, mode: str, symbol: str, octave_shift: int = 0) -> list[int]:
    root = _root_for_degree(tonic, mode, _degree_for(symbol)) + octave_shift * 12
    # For V in minor, raise leading tone (already in harmonic minor scale on degree 5? deg5=7 from tonic in harmonic)
    intervals = _quality_for(symbol, mode)
    pitches = [root + iv for iv in intervals]
    return pitches


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
    # Snap to catalog tonic MIDI (same pitch class)
    catalog = TONICS[letter]
    while catalog % 12 != rel_tonic % 12:
        catalog += 1
    # Prefer nearby octave to original tonic
    while catalog - tonic > 6:
        catalog -= 12
    while tonic - catalog > 6:
        catalog += 12
    return f"{letter} {rel_mode}", rel_mode, catalog
