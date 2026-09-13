"""M5 functional harmony grammar — function regions and chord choice weights."""

from __future__ import annotations

import random
from typing import Any

from app.engine.harmony_vocab import MAJOR_VOCAB, MINOR_VOCAB, UnknownChordSymbol, chord_spec

# Function-region transitions (not chord-to-chord) — MUSICALITY_OVERHAUL.md §5.1
FUNCTION_TRANSITIONS: dict[str, dict[str, float]] = {
    "tonic": {"subdominant": 0.50, "dominant": 0.28, "tonic": 0.12, "colour": 0.10},
    "subdominant": {"dominant": 0.62, "subdominant": 0.20, "colour": 0.12, "tonic": 0.06},
    "dominant": {"tonic": 0.72, "dominant": 0.16, "colour": 0.08, "subdominant": 0.04},
    "colour": {"dominant": 0.48, "subdominant": 0.30, "tonic": 0.22},
}

# Within-function chord choice weights — MUSICALITY_OVERHAUL.md §5.1
CHORD_CHOICE: dict[str, dict[str, float]] = {
    "tonic": {"i": 0.55, "i6": 0.12, "iM7": 0.08, "i7": 0.08, "III": 0.12, "I": 0.05},
    "subdominant": {
        "iv": 0.42,
        "iiø7": 0.18,
        "VI": 0.14,
        "bVII": 0.10,
        "iv6": 0.08,
        "bII": 0.05,
        "IV": 0.03,
    },
    "dominant": {
        "V7": 0.44,
        "V7b9": 0.26,
        "V": 0.12,
        "vii°7": 0.10,
        "subV7": 0.05,
        "Ger+6": 0.03,
    },
    "colour": {
        "V7/iv": 0.28,
        "V7/V": 0.26,
        "V7/VI": 0.20,
        "V7/III": 0.14,
        "III+": 0.12,
    },
}

_SEVENTH_HINTS = ("7", "°")
_DISSONANCE_BOOST: dict[str, float] = {
    "low": 0.85,
    "medium": 1.0,
    "high": 1.35,
}


def _vocab_for_mode(mode: str) -> dict[str, Any]:
    return MINOR_VOCAB if mode == "minor" else MAJOR_VOCAB


def _weighted_choice(rng: random.Random, weights: dict[str, float]) -> str:
    names = list(weights.keys())
    ws = [weights[n] for n in names]
    return rng.choices(names, weights=ws, k=1)[0]


def _renormalize(weights: dict[str, float]) -> dict[str, float]:
    total = sum(weights.values())
    if total <= 0:
        return weights
    return {k: v / total for k, v in weights.items()}


def pick_function_transition(
    rng: random.Random,
    current_function: str,
    *,
    colour_allowed: bool,
) -> str:
    """Sample the next harmonic function region from transition weights."""
    transitions = dict(FUNCTION_TRANSITIONS.get(current_function, FUNCTION_TRANSITIONS["tonic"]))
    if not colour_allowed:
        transitions.pop("colour", None)
        transitions = _renormalize(transitions)
    return _weighted_choice(rng, transitions)


def _tendency_multiplier(symbol: str, function: str, tendencies: dict[str, Any]) -> float:
    mult = 1.0
    seventh_freq = float(tendencies.get("seventh_frequency", 0.4))
    if any(h in symbol for h in _SEVENTH_HINTS):
        mult *= 0.75 + 0.5 * seventh_freq

    dissonance = str(tendencies.get("dissonance_level", "low")).lower()
    if dissonance in _DISSONANCE_BOOST and symbol in ("V7b9", "vii°7", "iiø7", "Ger+6", "III+"):
        mult *= _DISSONANCE_BOOST[dissonance]

    if function == "colour":
        sec_rate = float(tendencies.get("secondary_dominant_rate", 0.2))
        mult *= 0.8 + 0.4 * sec_rate

    chromatic = float(tendencies.get("chromatic_density", 0.15))
    if symbol in ("iM7", "i7", "i6", "iv6", "subV7", "Ger+6"):
        mult *= 0.85 + 0.3 * chromatic

    return mult


def pick_chord_for_function(
    rng: random.Random,
    function: str,
    mode: str,
    tendencies: dict[str, Any],
) -> str:
    """Sample a chord symbol for a function region; symbol must exist in mode vocab."""
    base = dict(CHORD_CHOICE.get(function, CHORD_CHOICE["tonic"]))
    vocab = _vocab_for_mode(mode)
    weights: dict[str, float] = {}
    for symbol, w in base.items():
        if symbol not in vocab:
            continue
        try:
            chord_spec(symbol, mode)
        except UnknownChordSymbol:
            continue
        weights[symbol] = w * _tendency_multiplier(symbol, function, tendencies)

    if not weights:
        fallback = "i" if mode == "minor" else "I"
        return fallback if fallback in vocab else next(iter(vocab))

    return _weighted_choice(rng, weights)
