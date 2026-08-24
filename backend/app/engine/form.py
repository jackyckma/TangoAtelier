"""Phrase-driven form and harmony planning (M2)."""

from __future__ import annotations

import random
from dataclasses import asdict, dataclass, field
from typing import Any, Literal

from app.engine.catalog import PROGRESSIONS_MAJOR, PROGRESSIONS_MINOR
from app.engine.harmony import relative_key
from app.engine.melody.expectancy import allow_deceptive_cadence, harmonic_rhythm_hold

CadenceKind = Literal["half", "imperfect", "deceptive", "authentic", "open"]

CADENCE_PLANS: dict[int, list[CadenceKind]] = {
    2: ["half", "authentic"],
    3: ["half", "imperfect", "authentic"],
    4: ["half", "imperfect", "half", "authentic"],
}

CADENCE_CHORDS: dict[str, dict[str, list[str]]] = {
    "half": {"minor": ["V7"], "major": ["V7"]},
    "imperfect": {"minor": ["V7", "i"], "major": ["V7", "I"]},
    "deceptive": {"minor": ["V7", "VI"], "major": ["V7", "vi"]},
    "authentic": {"minor": ["V7b9", "i"], "major": ["V7", "I"]},
    "open": {"minor": ["iv"], "major": ["IV"]},
}

CADENCE_ROLE: dict[str, str] = {
    "half": "half",
    "imperfect": "authentic",
    "deceptive": "deceptive",
    "authentic": "authentic",
    "open": "half",
}

# Sections that use phrase-driven fill (not bridge pedal)
_PHRASE_SECTIONS = frozenset(
    {"A", "B", "A_prime", "A2", "variacion", "estribillo", "intro", "coda", "cadence"}
)


@dataclass
class Phrase:
    index: int
    bar_from: int  # 1-based piece bar index
    bars: int
    cadence: str
    role: str  # question | answer
    anacrusis_beats: float = 0.0


@dataclass
class SectionPlan:
    section: str
    key: str
    mode: str
    tonic: int
    progression_id: str
    progression: list[str]
    modulation: str | None = None
    phrases: list[Phrase] = field(default_factory=list)
    bar_from: int = 1
    bar_to: int = 1
    bars_per_chord: int = 1


def _extend_plan(n: int) -> list[CadenceKind]:
    pattern: list[CadenceKind] = ["half", "imperfect", "half", "authentic"]
    out: list[CadenceKind] = []
    while len(out) < n:
        out.extend(pattern)
    if out and out[-1] != "authentic":
        out[-1] = "authentic"
    return out[:n]


def _map_progression_symbols(symbols: list[str], target_mode: str) -> list[str]:
    _TO_MINOR = {
        "I": "i",
        "ii": "iiø7",
        "iii": "iii",
        "IV": "iv",
        "V": "V",
        "V7": "V7",
        "V7b9": "V7b9",
        "vi": "VI",
        "vii°": "vii°",
        "vii°7": "vii°7",
        "i": "i",
        "iv": "iv",
        "VI": "VI",
        "III": "III",
        "iiø7": "iiø7",
        "bVII": "bVII",
        "V7/IV": "V7/iv",
        "V7/V": "V7/V",
        "V7/ii": "V7/V",
        "bII": "bII",
    }
    _TO_MAJOR = {
        "i": "I",
        "i6": "I",
        "i7": "I",
        "iM7": "I",
        "iiø7": "ii",
        "iii": "iii",
        "III": "iii",
        "iv": "IV",
        "iv6": "IV",
        "IV": "IV",
        "V": "V",
        "V7": "V7",
        "V7b9": "V7",
        "vi": "vi",
        "VI": "vi",
        "bVII": "bVII",
        "vii°": "vii°",
        "vii°7": "vii°",
        "V7/iv": "V7/IV",
        "V7/V": "V7/V",
        "V7/VI": "V7/iii",
        "V7/III": "V7/vi",
        "V7/IV": "V7/IV",
        "I": "I",
        "bII": "bII",
    }
    table = _TO_MINOR if target_mode == "minor" else _TO_MAJOR
    return [table.get(s, s) for s in symbols]


def _progression_for_mode(prog_id: str, mode: str, fallback: list[str]) -> list[str]:
    """Same progression_id in the sounding key when catalog has a parallel entry."""
    table = PROGRESSIONS_MINOR if mode == "minor" else PROGRESSIONS_MAJOR
    if prog_id in table:
        return list(table[prog_id])
    mapped = _map_progression_symbols(fallback, mode)
    # Reject unmapped minor-only colour (e.g. iM7) — fall back to a stable twin
    from app.engine.harmony_vocab import MAJOR_VOCAB, MINOR_VOCAB, normalize_symbol

    vocab = MINOR_VOCAB if mode == "minor" else MAJOR_VOCAB
    if all(normalize_symbol(s) in vocab for s in mapped):
        return mapped
    if mode == "major":
        return list(table.get("descending_fifths") or table["I-IV-V-I"])
    return list(table.get("descending_fifths") or table["i-iv-V7-i"])


def pick_progression(
    rng: random.Random, mode: str, progression_id: str | None
) -> tuple[str, list[str]]:
    table = PROGRESSIONS_MINOR if mode == "minor" else PROGRESSIONS_MAJOR
    other = PROGRESSIONS_MAJOR if mode == "minor" else PROGRESSIONS_MINOR
    if progression_id and progression_id != "random":
        if progression_id in table:
            return progression_id, list(table[progression_id])
        if progression_id in other:
            return progression_id, _map_progression_symbols(list(other[progression_id]), mode)
    pid = rng.choice(list(table.keys()))
    return pid, list(table[pid])


def alternate_progression(
    rng: random.Random, mode: str, current_id: str
) -> tuple[str, list[str]]:
    table = PROGRESSIONS_MINOR if mode == "minor" else PROGRESSIONS_MAJOR
    choices = [k for k in table if k != current_id]
    pid = rng.choice(choices or list(table.keys()))
    return pid, list(table[pid])


def harmonic_rhythm_for_bar(
    local_bar: int,
    phrase_bars: int,
    *,
    drama_tag: str = "normal",
    section_name: str = "A",
) -> int:
    """0 = hold previous chord; 1 = new chord slot — expectancy-gated."""
    return harmonic_rhythm_hold(
        local_bar,
        phrase_bars,
        drama_tag=drama_tag,
        section_name=section_name,
    )


def plan_phrases(
    *,
    section_name: str,
    bars: int,
    dance_type: str,
    bar_from_1based: int,
    pause_bars: set[int],
    rng: random.Random,
) -> list[Phrase]:
    phrase_len = 8 if dance_type == "vals" else 4
    chunks: list[int] = []
    local = 0
    while local < bars:
        abs_bar = bar_from_1based - 1 + local
        if abs_bar in pause_bars:
            local += 1
            continue
        remaining = bars - local
        length = min(phrase_len, remaining)
        if length <= 0:
            break
        if length == 1 and local + 1 < bars and (bar_from_1based + local) not in pause_bars:
            length = 2
        chunks.append(min(length, remaining))
        local += chunks[-1]

    n = len(chunks) or 1
    if not chunks:
        chunks = [bars]

    cadences: list[CadenceKind]
    if section_name == "intro":
        cadences = ["open"] * n
        cadences[-1] = "authentic"
    elif section_name == "bridge":
        cadences = ["half"] * n
    elif section_name == "coda":
        cadences = (["half"] * (n - 1) + ["authentic"]) if n > 1 else ["authentic"]
    elif section_name == "cadence":
        cadences = (["half"] * (n - 1) + ["authentic"]) if n > 1 else ["authentic"]
    else:
        cadences = list(CADENCE_PLANS.get(n) or _extend_plan(n))
        for i in range(n):
            if allow_deceptive_cadence(
                section_name=section_name,
                phrase_index=i,
                n_phrases=n,
                energy_hint=0.6 if section_name in ("B", "A_prime", "variacion") else 0.4,
            ):
                cadences[i] = "deceptive"
            elif cadences[i] == "deceptive":
                # Plans no longer default to deceptive; belt-and-suspenders
                cadences[i] = "imperfect" if i < n - 1 else "authentic"

    bar_cursor = bar_from_1based
    phrases: list[Phrase] = []
    for i, plen in enumerate(chunks):
        cad = cadences[i] if i < len(cadences) else "authentic"
        role = "question" if i % 2 == 0 else "answer"
        phrases.append(
            Phrase(
                index=i,
                bar_from=bar_cursor,
                bars=plen,
                cadence=cad,
                role=role,
                anacrusis_beats=0.0,
            )
        )
        bar_cursor += plen
    return phrases


def fill_phrase_harmony(
    phrase: Phrase,
    *,
    mode: str,
    progression_template: list[str],
    section_name: str = "A",
) -> tuple[list[str], dict[int, str]]:
    """Return local-bar symbols and cadence roles (local index → role)."""
    symbols = [""] * phrase.bars
    roles: dict[int, str] = {}
    cadence_syms = CADENCE_CHORDS.get(phrase.cadence, {}).get(mode, ["i" if mode == "minor" else "I"])
    start = max(0, phrase.bars - len(cadence_syms))
    for offset, sym in enumerate(cadence_syms):
        idx = start + offset
        if idx < phrase.bars:
            symbols[idx] = sym
            roles[idx] = CADENCE_ROLE.get(phrase.cadence, "authentic")

    prog_i = 0
    prev = progression_template[0] if progression_template else ("i" if mode == "minor" else "I")
    for local in range(phrase.bars):
        if symbols[local]:
            prev = symbols[local]
            continue
        if (
            harmonic_rhythm_for_bar(
                local, phrase.bars, drama_tag="normal", section_name=section_name
            )
            == 0
            and local > 0
        ):
            symbols[local] = prev
            continue
        sym = progression_template[prog_i % len(progression_template)]
        prog_i += 1
        symbols[local] = sym
        prev = sym

    for local in range(phrase.bars):
        if not symbols[local]:
            symbols[local] = prev

    return symbols, roles


def fill_section_harmony(
    *,
    section_name: str,
    bars: int,
    mode: str,
    progression_template: list[str],
    phrases: list[Phrase],
    bar_from_1based: int,
    pause_bars: set[int],
) -> tuple[list[str], dict[int, str]]:
    """Build one chord symbol per bar for the section."""
    if section_name == "bridge":
        # Pure V7 pedal — audible pivot before relative major/minor B
        dominant = "V7"
        symbols = [dominant] * bars
        roles = {i: "half" for i in range(max(0, bars - 2), bars)}
        return symbols, roles

    if section_name == "intro":
        tonic = "i" if mode == "minor" else "I"
        symbols = [tonic] * bars
        roles = {bars - 1: "authentic"} if bars else {}
        return symbols, roles

    out = [""] * bars
    roles: dict[int, str] = {}
    local_offset = 0
    for phrase in phrases:
        phrase_syms, phrase_roles = fill_phrase_harmony(
            phrase,
            mode=mode,
            progression_template=progression_template,
            section_name=section_name,
        )
        for i, sym in enumerate(phrase_syms):
            global_local = local_offset + i
            if global_local >= bars:
                break
            abs_bar = bar_from_1based - 1 + global_local
            is_cadence_slot = i in phrase_roles
            if abs_bar in pause_bars and not is_cadence_slot:
                continue
            out[global_local] = sym
            if is_cadence_slot:
                roles[global_local] = phrase_roles[i]
        local_offset += phrase.bars

    prev = progression_template[0] if progression_template else ("i" if mode == "minor" else "I")
    for i in range(bars):
        if not out[i]:
            out[i] = prev
        prev = out[i]

    if section_name == "coda" and bars > 0:
        out[-1] = "i" if mode == "minor" else "I"
        roles[bars - 1] = "authentic"
        if bars >= 2:
            out[-2] = "V7"
            roles[bars - 2] = "approach"

    return out, roles


def _apply_relative_modulation(
    rng: random.Random,
    *,
    home_key: str,
    home_mode: str,
    home_tonic: int,
    home_prog_id: str,
    home_progression: list[str],
    user_locked_progression: bool,
) -> tuple[str, str, int, str, list[str], str | None]:
    """Prefer relative major/minor; keep locked progression symbols mapped to target mode."""
    rel = relative_key(home_key, home_mode, home_tonic)
    if rel is None:
        if user_locked_progression:
            return home_key, home_mode, home_tonic, home_prog_id, list(home_progression), None
        prog_id, progression = alternate_progression(rng, home_mode, home_prog_id)
        return home_key, home_mode, home_tonic, prog_id, progression, "progression_change"

    key_name, mode, tonic = rel
    modulation = "relative_major" if mode == "major" else "relative_minor"
    # Continuity: keep the same progression family mapped to the relative key —
    # do not shop a new template just to sound "different".
    return (
        key_name,
        mode,
        tonic,
        home_prog_id,
        _progression_for_mode(home_prog_id, mode, home_progression),
        modulation,
    )


def plan_section_harmony(
    rng: random.Random,
    *,
    section_name: str,
    home_key: str,
    home_mode: str,
    home_tonic: int,
    home_prog_id: str,
    home_progression: list[str],
    user_locked_progression: bool,
    piece_harmony: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Per-section key + progression pool (modulation for B)."""
    piece_harmony = piece_harmony if piece_harmony is not None else {}
    key_name, mode, tonic = home_key, home_mode, home_tonic
    prog_id, progression = home_prog_id, list(home_progression)
    modulation: str | None = None

    if section_name in ("intro", "coda", "A", "variacion"):
        return {
            "section": section_name,
            "key": key_name,
            "mode": mode,
            "tonic": tonic,
            "progression_id": prog_id,
            "progression": progression,
            "modulation": None,
        }

    if section_name == "A2":
        contrast = piece_harmony.get("contrast")
        if contrast and str(contrast.get("modulation") or "").startswith("relative"):
            return {
                "section": "A2",
                "key": str(contrast["key"]),
                "mode": str(contrast["mode"]),
                "tonic": int(contrast["tonic"]),
                "progression_id": str(contrast["progression_id"]),
                "progression": list(contrast["progression"]),
                "modulation": "relative_continuation",
            }
        return {
            "section": section_name,
            "key": key_name,
            "mode": mode,
            "tonic": tonic,
            "progression_id": prog_id,
            "progression": progression,
            "modulation": None,
        }

    if section_name in ("A_prime",):
        return {
            "section": section_name,
            "key": key_name,
            "mode": mode,
            "tonic": tonic,
            "progression_id": prog_id,
            "progression": progression,
            "modulation": "recap",
        }

    if section_name == "bridge":
        return {
            "section": section_name,
            "key": key_name,
            "mode": mode,
            "tonic": tonic,
            "progression_id": "bridge_dominant",
            "progression": ["V7"],
            "modulation": "bridge_dominant",
        }

    if section_name == "B":
        cached = piece_harmony.get("contrast")
        if cached is not None:
            out = dict(cached)
            out["section"] = "B"
            return out

        (
            key_name,
            mode,
            tonic,
            prog_id,
            progression,
            modulation,
        ) = _apply_relative_modulation(
            rng,
            home_key=home_key,
            home_mode=home_mode,
            home_tonic=home_tonic,
            home_prog_id=home_prog_id,
            home_progression=home_progression,
            user_locked_progression=user_locked_progression,
        )

        plan = {
            "section": "B",
            "key": key_name,
            "mode": mode,
            "tonic": tonic,
            "progression_id": prog_id,
            "progression": progression,
            "modulation": modulation,
        }
        piece_harmony["contrast"] = {
            k: plan[k]
            for k in ("key", "mode", "tonic", "progression_id", "progression", "modulation")
        }
        return plan

    if section_name == "estribillo":
        return {
            "section": section_name,
            "key": key_name,
            "mode": mode,
            "tonic": tonic,
            "progression_id": prog_id,
            "progression": progression,
            "modulation": "estribillo",
        }

    return {
        "section": section_name,
        "key": key_name,
        "mode": mode,
        "tonic": tonic,
        "progression_id": prog_id,
        "progression": progression,
        "modulation": modulation,
    }


def phrase_to_dict(p: Phrase) -> dict[str, Any]:
    d = asdict(p)
    return d


def phrase_context_for_bar(
    phrases: list[Phrase],
    *,
    section_start_bar: int,
    local_bar: int,
) -> dict[str, Any] | None:
    """Section-local bar index → M2 phrase metadata for LH phrase gating."""
    abs_bar = section_start_bar + local_bar
    for p in phrases:
        start = p.bar_from - 1
        end = start + p.bars
        if start <= abs_bar < end:
            offset = abs_bar - start
            return {
                "phrase_index": p.index,
                "phrase_local_bar": offset,
                "phrase_bars": p.bars,
                "phrase_role": p.role,
                "phrase_end": offset == p.bars - 1,
            }
    return None


def build_section_harmony(
    rng: random.Random,
    *,
    section_name: str,
    section_bars: int,
    section_start_bar: int,
    dance_type: str,
    sec: dict[str, Any],
    pause_bars: set[int],
) -> tuple[list[str], dict[int, str], list[Phrase]]:
    """Phrase plan + per-bar chord symbols for one section."""
    bar_from_1 = section_start_bar + 1
    phrases = plan_phrases(
        section_name=section_name,
        bars=section_bars,
        dance_type=dance_type,
        bar_from_1based=bar_from_1,
        pause_bars=pause_bars,
        rng=rng,
    )
    symbols, roles = fill_section_harmony(
        section_name=section_name,
        bars=section_bars,
        mode=str(sec["mode"]),
        progression_template=list(sec["progression"]),
        phrases=phrases,
        bar_from_1based=bar_from_1,
        pause_bars=pause_bars,
    )
    return symbols, roles, phrases
