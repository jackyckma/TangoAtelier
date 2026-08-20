from __future__ import annotations

import random
from typing import Any, Literal

from app.engine.catalog import (
    DANCE_TYPES,
    FORMS,
    KEYS,
    KEYS_MAJOR,
    KEYS_MINOR,
    PROGRESSIONS_MAJOR,
    PROGRESSIONS_MINOR,
)
from app.engine.form import (
    build_section_harmony,
    phrase_to_dict,
    pick_progression,
    plan_section_harmony,
)
from app.engine.harmony import (
    HARMONIC_MINOR,
    MAJOR_SCALE,
    TONICS,
    chord_pitches,
)
from app.engine.melody import (
    ChordSlot,
    DENSITY_NOTES_PER_BAR,
    MELODY_HI,
    MELODY_LO,
    clamp_melody as _clamp_melody,
    generate_phrase_melody,
    intervals_to_adjacent_steps,
    make_pitch_cell,
    melody_notes_to_dicts,
    sample_piece_cells,
    sample_rhythm_cell,
)

Level = Literal["low", "medium", "high"]

# Re-exported for critic / tests (canonical defs live in app.engine.melody).
# Stronger spread so medium/high actually change contours & reuse behaviour
VARIATION_STRENGTH = {"low": 0.25, "medium": 0.55, "high": 0.85}

_LEVEL_UP: dict[Level, Level] = {"low": "medium", "medium": "high", "high": "high"}


def _roll_a_prime_elaboration(rng: random.Random, variation: Level) -> dict[str, Any]:
    """E2: schedule how the recap is richer than A — render executes most of it."""
    var = VARIATION_STRENGTH[variation]
    lh = "walking" if rng.random() < (0.55 + 0.25 * var) else "busier"
    return {
        "ornament_boost": round(0.22 + 0.2 * var, 3),
        "lh_upgrade": lh,
        "dynamics_boost": round(0.14 + 0.12 * var, 3),
        "density_bump": True,
        "register_lift": rng.random() < (0.4 + 0.35 * var),
    }


def _parse_key(key_name: str) -> tuple[str, str, int]:
    parts = key_name.strip().split()
    tonic_letter = parts[0]
    mode = "minor" if len(parts) > 1 and parts[1].startswith("min") else "major"
    tonic = TONICS.get(tonic_letter, 57)
    return key_name if " " in key_name else f"{tonic_letter} {mode}", mode, tonic


def _progression_mode_for_id(progression_id: str) -> str | None:
    in_min = progression_id in PROGRESSIONS_MINOR
    in_maj = progression_id in PROGRESSIONS_MAJOR
    if in_min and not in_maj:
        return "minor"
    if in_maj and not in_min:
        return "major"
    return None


def _scale_pool(tonic: int, mode: str) -> list[int]:
    intervals = HARMONIC_MINOR if mode == "minor" else MAJOR_SCALE
    return [
        _clamp_melody(tonic + iv + oct * 12)
        for oct in (-1, 0, 1, 2)
        for iv in intervals
    ]


def _chord_pool(tonic: int, mode: str, symbol: str) -> list[int]:
    # Chord tones across the melody register (not a single cramped octave)
    return [
        _clamp_melody(p + oct)
        for p in chord_pitches(tonic, mode, symbol)
        for oct in (0, 12, 24)
    ]


def _nearest(pool: list[int], target: int) -> int:
    return min(pool, key=lambda p: abs(p - target))


def _pc(p: int) -> int:
    return int(p) % 12


def _phrase_register_bias(
    rng: random.Random,
    *,
    section_name: str,
    role: Literal["question", "answer"],
    drama_high: bool,
    variation: float,
) -> int:
    """Skeleton-level register plan: songs move between mid and high phrases."""
    if drama_high:
        return 12
    if section_name in ("B", "A_prime") and role == "question":
        return 12 if rng.random() < 0.7 else 0
    if section_name == "A" and role == "question" and rng.random() < 0.25 + variation * 0.2:
        return 12
    if role == "answer" and rng.random() < 0.2:
        return -12
    return 0


def _roll_piece_motif(
    rng: random.Random,
    *,
    dance_type: str,
    tonic: int,
    mode: str,
    contour: str | None = None,
) -> dict[str, Any]:
    """Piece identity from M4 PitchCell + RhythmCell (freely paired)."""
    # Map legacy contrast names → M4 contours
    legacy_map = {
        "arch": "arch",
        "rise": "ascent",
        "fall": "descent",
        "wave": "arch",
        "neighbor": "plateau",
        "leap_settle": "leap_fill",
        "descent": "descent",
        "ascent": "ascent",
        "plateau": "plateau",
        "leap_fill": "leap_fill",
    }
    contour_name = legacy_map.get(contour or "", None)
    if contour_name is None:
        from app.engine.melody.structural import CONTOUR_WEIGHTS

        weights = CONTOUR_WEIGHTS.get(dance_type, CONTOUR_WEIGHTS["tango"])
        names = list(weights.keys())
        contour_name = rng.choices(names, weights=[weights[n] for n in names], k=1)[0]

    pitch_cell = make_pitch_cell(rng, contour_name)
    intervals = list(pitch_cell.intervals)
    steps = intervals_to_adjacent_steps(intervals)
    n_notes = max(2, len(intervals))

    r_q = sample_rhythm_cell(rng, dance_type)
    r_a = sample_rhythm_cell(rng, dance_type)

    def fit(onsets: list[float], n: int) -> list[float]:
        slots = [o for o in onsets if o >= 0]
        if len(slots) >= n:
            return slots[:n]
        extras = [0.0, 0.5, 1.0, 1.5, 0.75, 2.0]
        out = list(slots)
        for e in extras:
            if len(out) >= n:
                break
            if e not in out:
                out.append(e)
        return sorted(out[:n])

    start_degree = rng.choice([0, 0, 2, 4, 1, 3])
    scale = _scale_pool(tonic, mode)
    head = scale[min(start_degree, len(scale) - 1)]

    return {
        "steps": steps,
        "intervals": intervals,
        "n_notes": n_notes,
        "contour": contour_name,
        "rhythm_question": fit(list(r_q.onsets), n_notes),
        "rhythm_answer": fit(list(r_a.onsets), max(2, n_notes - 1)),
        "rhythm_cell_q": r_q.id,
        "rhythm_cell_a": r_a.id,
        "sequence_interval": rng.choice([0, 0, 2, 2, 3, 5, 7]),
        "head_pitch": int(head),
        "dance_type": dance_type,
    }


def _export_motivic_cell(cell: dict[str, Any]) -> dict[str, Any]:
    return {
        "steps": list(cell.get("steps") or []),
        "intervals": list(cell.get("intervals") or []),
        "n_notes": cell.get("n_notes"),
        "contour": cell.get("contour"),
        "sequence_interval": cell.get("sequence_interval"),
        "rhythm_question": list(cell.get("rhythm_question") or []),
        "rhythm_answer": list(cell.get("rhythm_answer") or []),
        "head_pitch": cell.get("head_pitch"),
        "development_axis": (
            "0=plain, 1=slight, 2=decorated, 3=dense; "
            "rises with bar index and drama energy; A_prime starts +1"
        ),
    }


_CONTRAST_PREF = {
    "arch": ("descent", "plateau", "leap_fill", "ascent"),
    "ascent": ("descent", "arch", "plateau", "leap_fill"),
    "descent": ("ascent", "arch", "leap_fill", "plateau"),
    "plateau": ("leap_fill", "descent", "arch", "ascent"),
    "leap_fill": ("plateau", "arch", "descent", "ascent"),
}


def _steps_too_similar(a: list[int], b: list[int]) -> bool:
    if not a or not b:
        return False
    n = min(len(a), len(b))
    same = sum(1 for i in range(n) if a[i] == b[i])
    inv = sum(1 for i in range(n) if a[i] == -b[i])
    return same >= n - 1 or inv >= n - 1


def _roll_motivic_cells(
    rng: random.Random,
    dance_type: str,
    tonic: int,
    mode: str,
) -> list[dict[str, Any]]:
    """1–3 identifiable cells; cell 0 is the home theme (legacy motif).

    Contrast cells keep their own contour/rhythm — not a mere invert of home
    (that made every B sound like the same mold flipped).
    """
    n = rng.choice([2, 2, 2, 3, 3, 1])
    home = _roll_piece_motif(rng, dance_type=dance_type, tonic=tonic, mode=mode)
    cells: list[dict[str, Any]] = [home]
    if n >= 2:
        prefs = _CONTRAST_PREF.get(str(home.get("contour") or "arch"), ("wave", "fall", "rise"))
        contrast = None
        for _ in range(4):
            want = rng.choice(prefs)
            candidate = _roll_piece_motif(
                rng, dance_type=dance_type, tonic=tonic, mode=mode, contour=want
            )
            if not _steps_too_similar(list(home["steps"]), list(candidate["steps"])):
                contrast = candidate
                break
            contrast = candidate
        assert contrast is not None
        cells.append(contrast)
    if n >= 3:
        # Tag / coda cell: home head + flipped tail (recallable fragment, not a new song)
        coda_cell = _roll_piece_motif(
            rng, dance_type=dance_type, tonic=tonic, mode=mode, contour=str(home.get("contour"))
        )
        coda_cell["steps"] = list(home["steps"])
        if len(coda_cell["steps"]) > 2:
            coda_cell["steps"] = coda_cell["steps"][:2] + [-s for s in coda_cell["steps"][2:]]
        coda_cell["n_notes"] = home["n_notes"]
        coda_cell["rhythm_question"] = list(home["rhythm_question"])
        coda_cell["sequence_interval"] = int(home.get("sequence_interval") or 2)
        coda_cell["contour"] = f"tag_{home.get('contour') or 'arch'}"
        cells.append(coda_cell)
    return cells


def _motivic_cell_index_for_section(section_name: str, n_cells: int) -> int:
    n = max(1, int(n_cells))
    if section_name in ("intro", "A", "A_prime"):
        return 0
    if section_name in ("B", "bridge"):
        return min(1, n - 1)
    if section_name == "coda":
        return min(2, n - 1) if n >= 3 else 0
    return 0


def _motivic_development_level(
    *,
    local_bar: int,
    section_bars: int,
    drama_tag: str,
    energy: float,
    section_name: str,
) -> int:
    """0–3 surface intensity on a locked cell contour."""
    span = max(1, section_bars - 1)
    level = int(round(3 * max(0, local_bar) / span))
    if drama_tag in ("dense", "climax"):
        level += 1
    elif drama_tag in ("rise",) and energy >= 0.55:
        level += 1
    if energy >= 0.75:
        level += 1
    if section_name == "A_prime":
        level += 1
    return max(0, min(3, level))


def _density_for_development(base: Level, development: int, *, dance_type: str) -> Level:
    # At most one step — A′ richness is LH/ornament, not a note-count dump
    if dance_type == "vals":
        return base
    if development >= 3:
        return _LEVEL_UP[base]
    return base


def _step_density(prev: Level, wanted: Level) -> Level:
    """Adjacent phrases may move at most one density step."""
    order: list[Level] = ["low", "medium", "high"]
    pi = order.index(prev) if prev in order else 1
    wi = order.index(wanted) if wanted in order else 1
    if wi > pi + 1:
        return order[pi + 1]
    if wi < pi - 1:
        return order[pi - 1]
    return wanted


def _stamp_motivic_meta(
    notes: list[dict[str, Any]],
    *,
    section_name: str,
    start_bar: int,
    section_bars: int,
    beats_per_bar: int,
    cell_id: int | None,
    drama: dict[str, Any],
    interweave_bars: set[int] | None = None,
) -> list[dict[str, Any]]:
    iw = interweave_bars or set()
    energy_map = drama.get("energy") or {}
    for n in notes:
        n["section"] = section_name
        bar = int(float(n["start_beat"]) // max(beats_per_bar, 1))
        local = bar - start_bar
        tag = str(n.get("drama") or "normal")
        energy = float(energy_map.get(bar, 0.5))
        if cell_id is not None:
            n["motivic_cell_id"] = int(cell_id)
        n["motivic_development"] = _motivic_development_level(
            local_bar=local,
            section_bars=section_bars,
            drama_tag=tag,
            energy=energy,
            section_name=section_name,
        )
        if bar in iw:
            n["motivic_interweave"] = True
    return notes


def _realize_motif(
    rng: random.Random,
    motif: dict[str, Any],
    *,
    tonic: int,
    mode: str,
    symbol: str,
    start_pitch: int | None,
    transform: Literal["prime", "invert", "answer", "sequence"],
    register_bias: int = 0,
    sequence_semitones: int = 0,
    n: int | None = None,
    dance_type: str = "tango",
    key_offset: int = 0,
) -> list[int]:
    """Realize PitchCell interval DNA onto chord tones (intro/coda/tags)."""
    intervals = list(motif.get("intervals") or [])
    steps = list(motif.get("steps") or [])
    if not intervals and steps:
        acc = 0
        intervals = [0]
        for s in steps:
            acc += s
            intervals.append(acc)
    if transform in ("invert", "answer"):
        intervals = [-iv for iv in intervals]
        steps = [-s for s in steps]
    if transform == "answer" and rng.random() < 0.35 and intervals:
        intervals = list(reversed(intervals))
        base = intervals[0]
        intervals = [iv - base for iv in intervals]

    chord = _chord_pool(tonic, mode, symbol)
    scale = _scale_pool(tonic, mode)
    band_lo = 60 + register_bias
    band_hi = 79 + register_bias
    band_chord = [p for p in chord if band_lo <= p <= band_hi] or chord

    if start_pitch is None:
        start = _clamp_melody(
            int(motif.get("head_pitch", band_chord[0]))
            + register_bias
            + sequence_semitones
            + key_offset
        )
        start = _nearest(band_chord, start)
    else:
        start = _nearest(band_chord, start_pitch + sequence_semitones)

    pitches = [start]
    for iv in intervals[1:]:
        target = _clamp_melody(start + iv + sequence_semitones)
        prev = pitches[-1]
        if abs(target - prev) >= 5:
            pitches.append(_clamp_melody(target))
        else:
            cands = [p for p in scale if abs(p - prev) <= 3] or scale
            pitches.append(_nearest(cands, target))

    want = n if n is not None else int(motif.get("n_notes") or len(pitches))
    if dance_type == "vals":
        want = min(want, 3)
    if len(pitches) > want:
        idxs = [0]
        for k in range(1, want - 1):
            idxs.append(round(k * (len(pitches) - 1) / (want - 1)))
        idxs.append(len(pitches) - 1)
        pitches = [pitches[i] for i in dict.fromkeys(idxs)]
    while len(pitches) < want:
        prev = pitches[-1]
        step = [p for p in scale if 0 < abs(p - prev) <= 2]
        pitches.append(rng.choice(step) if step else _clamp_melody(prev + 2))

    for i in range(len(pitches) - 2):
        leap = pitches[i + 1] - pitches[i]
        if abs(leap) < 5:
            continue
        step = pitches[i + 2] - pitches[i + 1]
        unrecovered = (leap > 0 and step >= 0) or (leap < 0 and step <= 0)
        if unrecovered:
            recover_dir = -1 if leap > 0 else 1
            cands = [p for p in scale if 0 < (p - pitches[i + 1]) * recover_dir <= 2]
            if cands:
                pitches[i + 2] = cands[0]

    pitches[0] = _nearest(chord, pitches[0])
    pitches[-1] = _nearest(chord, pitches[-1])
    if transform == "answer":
        roots = [p for p in chord if _pc(p) == _pc(chord[0])]
        if roots and abs(pitches[-1] - roots[0]) <= 8:
            pitches[-1] = _nearest(roots, pitches[-1])
    return [_clamp_melody(p) for p in pitches[:want]]


def _section_spans(sections: list[tuple[str, int]]) -> dict[str, list[tuple[int, int]]]:
    """Map section name → list of (start_bar, end_bar_exclusive) 0-based spans."""
    spans: dict[str, list[tuple[int, int]]] = {}
    bar = 0
    for name, n in sections:
        spans.setdefault(name, []).append((bar, bar + n))
        bar += n
    return spans


def _build_structural_anchors(
    sections: list[tuple[str, int]],
    *,
    climax_bar: int,
) -> dict[str, Any]:
    """E9: explicit narrative targets (climax / A′ entry / final cadence / A suspense)."""
    spans = _section_spans(sections)
    total = sum(n for _, n in sections)
    a_spans = spans.get("A") or []
    a_prime = spans.get("A_prime") or []
    coda = spans.get("coda") or []
    a_end = (a_spans[0][1] - 1) if a_spans else max(0, climax_bar - 4)
    a_prime_entry = a_prime[0][0] if a_prime else climax_bar
    final_cadence = (coda[-1][1] - 1) if coda else total - 1
    return {
        "climax_bar": int(climax_bar),
        "a_prime_entry": int(a_prime_entry),
        "final_cadence": int(final_cadence),
        "a_end_suspense": int(a_end),
    }


def _lerp_between_anchors(total: int, targets: list[tuple[int, float]]) -> dict[int, float]:
    """Simplified bidirectional infill: linear interpolation between ordered anchors."""
    pts = sorted({0: 0.22, total - 1: 0.28, **{b: v for b, v in targets}}.items())
    energy: dict[int, float] = {}
    for i in range(total):
        if i <= pts[0][0]:
            energy[i] = pts[0][1]
            continue
        if i >= pts[-1][0]:
            energy[i] = pts[-1][1]
            continue
        lo_b, lo_v = pts[0]
        hi_b, hi_v = pts[-1]
        for k in range(len(pts) - 1):
            if pts[k][0] <= i <= pts[k + 1][0]:
                lo_b, lo_v = pts[k]
                hi_b, hi_v = pts[k + 1]
                break
        if hi_b == lo_b:
            energy[i] = lo_v
        else:
            t = (i - lo_b) / (hi_b - lo_b)
            energy[i] = lo_v + (hi_v - lo_v) * t
    return energy


def _roll_section_groove(rng: random.Random, dance_type: str) -> dict[str, dict[str, Any]]:
    """M10 / E12: form-level groove roles + LH fullness (no microtiming baked in).

    Roles drive continuous contrast runs at render time; colour_slots remain only
    as optional 1-bar spice markers at phrase ends for home sections.
    """
    # Preserve pre-M10 RNG budget: only tango drew once here; vals/milonga drew zero.
    # contrast_drive run length: 4 or 8 bars (tango), fixed 4 for vals/milonga.
    if dance_type == "vals":
        contrast_run = 4
    elif dance_type == "milonga":
        contrast_run = 4
    else:
        contrast_run = 8 if rng.random() < 0.4 else 4

    def _intent(
        role: str,
        lh: str,
        *,
        force_primary: bool = False,
        colour_slots: tuple[int, ...] = (),
        run: int | None = None,
    ) -> dict[str, Any]:
        out: dict[str, Any] = {
            "groove_role": role,
            "lh": lh,
            "force_primary": force_primary,
            "colour_slots": colour_slots,
        }
        if run is not None:
            out["contrast_run_bars"] = run
        return out

    if dance_type == "vals":
        return {
            "intro": _intent("home", "sparse", force_primary=True),
            "A": _intent("home", "steady", force_primary=True),
            "B": _intent("contrast_drive", "busy", run=contrast_run),
            "A_prime": _intent("home_elevated", "full", force_primary=True),
            "bridge": _intent("pivot", "sparse", force_primary=True),
            "coda": _intent("home_cadence", "cadence", force_primary=True),
            "variacion": _intent("contrast_drive", "busy", run=contrast_run),
        }
    if dance_type == "milonga":
        return {
            "intro": _intent("home", "sparse", force_primary=True),
            "A": _intent("home", "steady", colour_slots=(6,)),
            "B": _intent("contrast_drive", "busy", run=contrast_run),
            "A_prime": _intent("home_elevated", "full", colour_slots=(6,)),
            "bridge": _intent("pivot", "sparse", force_primary=True),
            "coda": _intent("home_cadence", "cadence", force_primary=True),
            "variacion": _intent("contrast_drive", "busy", run=contrast_run),
        }
    # tango — B = continuous drive block; A/A′ stay marcato with rare phrase-end spice
    return {
        "intro": _intent("home", "sparse", force_primary=True),
        "A": _intent("home", "steady", colour_slots=(6,)),
        "B": _intent("contrast_drive", "busy", run=contrast_run),
        "A_prime": _intent("home_elevated", "full", colour_slots=(6,)),
        "bridge": _intent("pivot", "sparse", force_primary=True),
        "coda": _intent("home_cadence", "cadence", force_primary=True),
        "variacion": _intent("contrast_drive", "busy", run=contrast_run),
    }


def _plan_motif_setup_payoff(
    rng: random.Random,
    sections: list[tuple[str, int]],
    *,
    climax_bar: int,
    n_cells: int,
) -> dict[str, Any]:
    """E10: schedule a short home-cell head early; recycle at climax or coda."""
    spans = _section_spans(sections)
    intro = spans.get("intro") or []
    a_spans = spans.get("A") or []
    coda = spans.get("coda") or []
    if intro:
        setup_bar = intro[0][1] - 1  # last intro bar — anacrusis into theme
        setup_section = "intro"
    elif a_spans:
        setup_bar = a_spans[0][0]
        setup_section = "A"
    else:
        setup_bar = 0
        setup_section = sections[0][0] if sections else "A"

    if rng.random() < 0.7:
        payoff_bar = int(climax_bar)
        payoff_section = "A_prime"
    elif coda:
        payoff_bar = coda[0][0]
        payoff_section = "coda"
    else:
        payoff_bar = int(climax_bar)
        payoff_section = "A_prime"

    return {
        "cell_id": 0,
        "setup_bar": int(setup_bar),
        "setup_section": setup_section,
        "payoff_bar": int(payoff_bar),
        "payoff_section": payoff_section,
        "setup_transform": "head",
        "payoff_transform": rng.choice(["prime", "prime", "sequence"]),
        "n_cells": int(n_cells),
    }


def _build_drama_map(
    rng: random.Random,
    sections: list[tuple[str, int]],
    *,
    dance_type: str,
    variation: Level,
) -> dict[str, Any]:
    """Tension arc: rise → anticipate → climax → release (not a sudden density dump)."""
    bar_sections: list[str] = []
    for name, n in sections:
        bar_sections.extend([name] * n)
    total = len(bar_sections)
    var = VARIATION_STRENGTH[variation]

    # Climax peak: late A_prime (or late thematic material)
    climax_candidates = [i for i, s in enumerate(bar_sections) if s == "A_prime"]
    if not climax_candidates:
        climax_candidates = [i for i, s in enumerate(bar_sections) if s in ("A", "B")]
    climax_bar = (
        climax_candidates[int(len(climax_candidates) * 0.72)]
        if climax_candidates
        else max(0, total - 5)
    )
    # Peak is short — 1–2 bars, not a 3-bar machine-gun
    climax_bars = {climax_bar}
    if var >= 0.5 and climax_bar + 1 < total and bar_sections[climax_bar + 1] == bar_sections[climax_bar]:
        climax_bars.add(climax_bar + 1)

    anchors = _build_structural_anchors(sections, climax_bar=climax_bar)

    # Approach window (bars before peak)
    rise_len = 3 if dance_type == "vals" else 4
    rise_bars = {
        i
        for i in range(max(0, climax_bar - rise_len), climax_bar - 1)
        if bar_sections[i] in ("A", "A_prime", "B")
    }
    anticipate_bar = climax_bar - 1
    anticipate_bars: set[int] = set()
    if anticipate_bar >= 0 and bar_sections[anticipate_bar] in ("A", "A_prime", "B"):
        anticipate_bars.add(anticipate_bar)
        rise_bars.discard(anticipate_bar)

    release_bars = {
        i
        for i in range(max(climax_bars) + 1, min(total, max(climax_bars) + 3))
        if bar_sections[i] in ("A", "A_prime", "B", "coda")
    }

    # Phrase-end air — never inside the approach/peak window (that kills anticipation)
    protected = rise_bars | anticipate_bars | climax_bars | release_bars
    pause_bars: set[int] = set()
    pause_budget = 0 if dance_type == "vals" else (
        (2 if dance_type == "tango" else 1) + int(var * 2)
    )
    pause_pool = [
        i
        for i, s in enumerate(bar_sections)
        if s in ("A", "A_prime", "B") and i % 4 == 3 and i not in protected
    ]
    rng.shuffle(pause_pool)
    for i in pause_pool[:pause_budget]:
        pause_bars.add(i)
    # One breath on the downbeat into coda (not every coda bar)
    for i, s in enumerate(bar_sections):
        if s == "coda" and (i == 0 or bar_sections[i - 1] != "coda"):
            if i > 0 and (i - 1) not in protected:
                pause_bars.add(i - 1)

    # Mid-piece colour bursts — away from the climax approach
    dense_bars: set[int] = set()
    dense_budget = 0 if dance_type in ("vals", "milonga") else 1 + int(var * 2)
    dense_pool = [
        i
        for i, s in enumerate(bar_sections)
        if s in ("A", "B")
        and i not in pause_bars
        and i not in protected
        and abs(i - climax_bar) > rise_len + 1
    ]
    rng.shuffle(dense_pool)
    for i in dense_pool[:dense_budget]:
        dense_bars.add(i)

    # E9: interpolate between structural anchors, then stamp local drama modifiers
    energy = _lerp_between_anchors(
        total,
        [
            (anchors["a_end_suspense"], 0.62),
            (anchors["a_prime_entry"], 0.55),
            (climax_bar, 1.0),
            (anchors["final_cadence"], 0.28),
        ],
    )
    for i in range(total):
        e = float(energy.get(i, 0.5))
        s = bar_sections[i]
        if s == "intro":
            e = min(e, 0.28)
        elif s == "bridge":
            e = 0.45 + 0.1 * (e - 0.5)
        if i in rise_bars:
            order = sorted(rise_bars)
            idx = order.index(i) if i in order else 0
            e = max(e, 0.55 + 0.3 * ((idx + 1) / max(1, len(order))))
        if i in anticipate_bars:
            e = 0.78
        if i in climax_bars:
            e = 1.0
        if i in release_bars:
            order = sorted(release_bars)
            idx = order.index(i) if i in order else 0
            e = min(e, 0.85 - 0.2 * ((idx + 1) / max(1, len(order))))
        if i in dense_bars:
            e = min(0.9, e + 0.1)
        if i in pause_bars:
            e = max(0.12, e - 0.3)
        energy[i] = round(e, 3)

    return {
        "climax_bars": sorted(climax_bars),
        "pause_bars": sorted(pause_bars),
        "dense_bars": sorted(dense_bars),
        "rise_bars": sorted(rise_bars),
        "anticipate_bars": sorted(anticipate_bars),
        "release_bars": sorted(release_bars),
        "energy": energy,
        "anchors": anchors,
    }


def _drama_tag_for_bar(bar: int, drama: dict[str, Any]) -> str:
    if bar in set(drama.get("pause_bars") or []):
        return "pause"
    if bar in set(drama.get("climax_bars") or []):
        return "climax"
    if bar in set(drama.get("anticipate_bars") or []):
        return "anticipate"
    if bar in set(drama.get("rise_bars") or []):
        return "rise"
    if bar in set(drama.get("release_bars") or []):
        return "release"
    if bar in set(drama.get("dense_bars") or []):
        return "dense"
    return "normal"


def _density_for_drama(base: Level, tag: str, *, dance_type: str) -> Level:
    """Drama shapes intensity via energy/register — not sudden note sprays."""
    order: list[Level] = ["low", "medium", "high"]
    idx = order.index(base) if base in order else 1
    if tag == "anticipate":
        # Thin the lead so the peak can land
        return order[max(0, idx - 1)]
    if tag == "rise":
        return base  # same note count, rising register/energy elsewhere
    if tag == "climax":
        if dance_type in ("vals", "milonga"):
            return base
        return order[min(2, idx + 1)]  # one step up only
    if tag == "release":
        return order[max(0, idx - 1)] if base == "high" else base
    if tag == "dense":
        return base  # energy/register only — extra attacks sound like a dump
    return base


def _register_for_drama(tag: str, phrase_i: int) -> int:
    """Gradual register climb into climax — no post-hoc octave dump."""
    if tag == "rise":
        return 5 if phrase_i % 2 == 0 else 7
    if tag == "anticipate":
        return 7
    if tag == "climax":
        return 12
    if tag == "release":
        return 0
    if tag == "dense":
        return 5
    return 0


def _tag_voice(notes: list[dict[str, Any]], voice: str) -> list[dict[str, Any]]:
    for n in notes:
        n["voice"] = voice
    return notes


def _sixteenth_slots(beats_per_bar: int) -> list[float]:
    """Beat offsets on a 16th-note grid inside one bar."""
    step = 0.25  # one sixteenth in quarter-note beats
    n = int(round(beats_per_bar / step))
    return [round(i * step, 3) for i in range(n)]


def _pick_grid_placements(
    rng: random.Random,
    *,
    beats_per_bar: int,
    count: int,
    density: Level,
    dance_type: str,
) -> list[float]:
    """Prefer strong beats, then &s, then 16ths — denser levels unlock finer slots."""
    if count <= 0:
        return []

    # Vals (~180 BPM): smooth quarters on 1–2–3; pickup cells skip beat 1
    if dance_type == "vals":
        if density == "low":
            cells = [[0.0, 2.0], [0.0], [0.0, 1.0], [1.0, 2.0], [2.0]]
        else:
            cells = [
                [0.0, 1.0, 2.0],
                [0.0, 2.0],
                [0.0, 1.0],
                [1.0, 2.0],
            ]
        base = list(rng.choice(cells))
        while len(base) < count:
            for cand in (0.0, 1.0, 2.0):
                if cand not in base:
                    base.append(cand)
                if len(base) >= count:
                    break
            else:
                break
        return sorted(base[: min(count, 3)])

    # Milonga: habanera / 3+3+2 only — generic 16ths fight the LH
    if dance_type == "milonga":
        habanera = [0.0, 0.75, 1.0, 1.5]
        triple = [0.0, 0.75, 1.5]
        cells = [habanera, triple, [0.0, 0.75, 1.5], [0.0, 1.0, 1.5]]
        base = list(rng.choice(cells))
        while len(base) < count:
            for cand in habanera:
                if cand not in base:
                    base.append(cand)
                if len(base) >= count:
                    break
            else:
                break
        return sorted(base[:count])

    slots = _sixteenth_slots(beats_per_bar)
    # Priority tiers (indices into 16th grid)
    strong = [i for i, s in enumerate(slots) if abs(s - round(s)) < 1e-9]  # on-beat
    eighths = [i for i, s in enumerate(slots) if abs((s * 2) - round(s * 2)) < 1e-9 and i not in strong]
    sixteenths = [i for i in range(len(slots)) if i not in strong and i not in eighths]

    ordered: list[int] = []
    if density == "low":
        pool = strong + eighths[: max(1, len(eighths) // 2)]
    elif density == "medium":
        pool = strong + eighths + sixteenths[::2]
    else:
        pool = strong + eighths + sixteenths

    # Always include beat 1
    if 0 in pool and 0 not in ordered:
        ordered.append(0)
    rng.shuffle(pool)
    for i in pool:
        if i not in ordered:
            ordered.append(i)
        if len(ordered) >= count:
            break
    # If still short, take remaining grid in order
    for i in range(len(slots)):
        if len(ordered) >= count:
            break
        if i not in ordered:
            ordered.append(i)
    placements = sorted(slots[i] for i in ordered[:count])
    return placements


def _emit_bar_notes(
    rng: random.Random,
    *,
    bar: int,
    beats_per_bar: int,
    pitches: list[int],
    density: Level,
    variation: Level,
    phrase_end: bool,
    role: str,
    dance_type: str,
    voice: str = "lead",
    tonic: int | None = None,
    mode: str | None = None,
    symbol: str | None = None,
    fixed_placements: list[float] | None = None,
) -> list[dict[str, Any]]:
    """Place given pitches on a grid (intro/coda helpers). Density caps length only."""
    if not pitches:
        return []

    target = DENSITY_NOTES_PER_BAR.get(dance_type, DENSITY_NOTES_PER_BAR["tango"])[density]
    if density == "low" and role == "answer":
        target = max(2 if dance_type != "vals" else 1, target - 1)
    if dance_type == "vals":
        target = min(target, 3)
    elif dance_type == "milonga":
        target = min(target, 5)
    if fixed_placements is not None:
        target = min(target, max(len(pitches), len(fixed_placements)))

    pitches = list(pitches[:target])
    # Pad with chord/scale neighbors only — densification belongs to Pass 2 connect
    if len(pitches) < target and tonic is not None and mode is not None and symbol is not None:
        chord = _chord_pool(tonic, mode, symbol)
        scale = _scale_pool(tonic, mode)
        while len(pitches) < target:
            prev = pitches[-1]
            nbr = [p for p in scale if 0 < abs(p - prev) <= 2] or chord
            pitches.append(_nearest(nbr, prev))

    if fixed_placements:
        # Keep motif rhythm identity; fill extras from dance grid if density needs more
        base = [p for p in fixed_placements if 0 <= p < beats_per_bar]
        if dance_type == "vals":
            base = [p for p in base if p in (0.0, 1.0, 2.0)]
        if len(base) >= len(pitches):
            placements = sorted(base[: len(pitches)])
        else:
            extra = _pick_grid_placements(
                rng,
                beats_per_bar=beats_per_bar,
                count=len(pitches) - len(base),
                density=density,
                dance_type=dance_type,
            )
            merged = list(base)
            for e in extra:
                if e not in merged:
                    merged.append(e)
            while len(merged) < len(pitches):
                if dance_type == "vals":
                    filled = False
                    for cand in (0.0, 1.0, 2.0):
                        if cand not in merged:
                            merged.append(cand)
                            filled = True
                            break
                    if not filled:
                        break
                else:
                    merged.append(min(beats_per_bar - 0.05, merged[-1] + 0.25))
            placements = sorted(merged[: len(pitches)])
            if dance_type == "vals" and len(placements) < len(pitches):
                pitches = pitches[: len(placements)]
    else:
        placements = _pick_grid_placements(
            rng,
            beats_per_bar=beats_per_bar,
            count=len(pitches),
            density=density,
            dance_type=dance_type,
        )
    notes: list[dict[str, Any]] = []
    for j, pitch in enumerate(pitches):
        start_local = placements[j] if j < len(placements) else 0.0
        is_last = j == len(pitches) - 1
        next_start = (
            placements[j + 1]
            if j + 1 < len(placements)
            else beats_per_bar
        )
        gap = max(0.05, next_start - start_local)
        if dance_type == "vals":
            dur = min(beats_per_bar - start_local, max(gap * 0.98, 0.92))
        elif dance_type == "milonga":
            if abs(start_local - 0.0) < 0.06:
                dur = min(0.72, max(gap * 0.92, 0.55))
            elif abs(start_local - 0.75) < 0.06:
                dur = min(0.22, gap * 0.85)
            else:
                dur = min(gap * 0.9, 0.45)
        elif density == "high":
            dur = min(gap, 0.28 if not is_last else max(0.35, gap * 0.9))
        elif density == "medium":
            dur = min(gap * 0.95, gap if is_last else 0.45)
        else:
            dur = min(beats_per_bar - start_local, max(gap * 0.9, 0.5))
        if is_last and phrase_end and density != "high":
            dur = max(dur, min(beats_per_bar - start_local, 0.75))
        if is_last and phrase_end and dance_type == "vals":
            dur = max(dur, min(beats_per_bar - start_local, 1.4))

        note: dict[str, Any] = {
            "pitch": int(_clamp_melody(pitch)),
            "start_beat": round(bar * beats_per_bar + start_local, 3),
            "duration_beats": round(max(0.08, dur), 3),
            "phrase_role": role,
            "voice": voice,
            "nct": "chord_tone",
            "structural_weight": 1.0 if j == 0 or is_last else 0.0,
        }
        if is_last and phrase_end:
            note["phrase_end"] = True
        notes.append(note)

    notes.sort(key=lambda n: n["start_beat"])
    return notes


def _partition_phrases(
    *,
    bars: int,
    start_bar: int,
    chords_for_bars: list[str],
    pause: set[int],
    dance_type: str,
) -> list[tuple[int, int]]:
    """Split a section into phrases (chord-aware), never across pauses.

    Tango/milonga: 2–4 bars. Vals: prefer one long spinning line (8–12).
    """
    phrases: list[tuple[int, int]] = []
    i = 0
    while i < bars:
        abs_i = start_bar + i
        if abs_i in pause:
            i += 1
            continue

        remaining = bars - i
        if dance_type == "vals":
            if remaining >= 8:
                target = remaining if remaining <= 12 else 8
            else:
                target = remaining
        else:
            # Prefer 4-bar lines on tango when aligned; milonga stays punchier at 2
            prefer_four = dance_type == "tango" and i % 4 == 0 and i + 4 <= bars
            target = 4 if prefer_four else 2

        length = 1
        for k in range(1, target):
            nxt = i + k
            if nxt >= bars or (start_bar + nxt) in pause:
                break
            length = k + 1
        # If we only got 1 bar but next is free, try to pair (avoid orphan bars)
        if length == 1 and i + 1 < bars and (start_bar + i + 1) not in pause:
            length = 2
        phrases.append((i, length))
        i += length
    return phrases


def _vals_onbeat_placements(
    rng: random.Random,
    count: int,
    *,
    preferred: list[float] | None,
    pickup: bool,
) -> list[float]:
    """Waltz melody lives on beats 1–2–3; pickup skips the downbeat."""
    count = max(1, min(3, count))
    legal = (0.0, 1.0, 2.0)
    pref = [p for p in (preferred or []) if p in legal]
    if pickup:
        if count <= 1:
            return [2.0]
        return [1.0, 2.0][:count]
    if len(pref) >= count:
        return sorted(pref[:count])
    defaults = {1: [0.0], 2: [0.0, 2.0], 3: [0.0, 1.0, 2.0]}
    if rng.random() < 0.25 and count == 2:
        return list(rng.choice(([0.0, 1.0], [0.0, 2.0], [1.0, 2.0])))
    return list(defaults[count])


def _emit_phrase(
    rng: random.Random,
    *,
    start_bar: int,
    n_bars: int,
    beats_per_bar: int,
    chords_for_bars: list[str],
    motif: dict[str, Any],
    density: Level,
    variation: Level,
    dance_type: str,
    tonic: int,
    mode: str,
    transform_q: Literal["prime", "invert", "answer", "sequence"],
    register_bias: int,
    sequence_semitones: int,
    start_pitch: int | None,
    key_offset: int = 0,
    cadence: str = "authentic",
    rhythm_cells: list | None = None,
    pause_frequency: str = "medium",
) -> tuple[list[dict[str, Any]], int]:
    """M4 three-pass phrase: structural → connect (decorate is render-only)."""
    # Apply motif transform / sequence / key to starting register
    prefer = str(motif.get("contour") or "")
    if prefer.startswith("tag_"):
        prefer = prefer[4:]
    intervals = list(motif.get("intervals") or [])
    if transform_q in ("invert", "answer") and intervals:
        intervals = [-iv for iv in intervals]
    if sequence_semitones:
        intervals = [iv + sequence_semitones for iv in intervals]

    adjusted_start = start_pitch
    if adjusted_start is not None:
        adjusted_start = _clamp_melody(int(adjusted_start) + key_offset + sequence_semitones)
    elif motif.get("head_pitch") is not None:
        adjusted_start = _clamp_melody(
            int(motif["head_pitch"]) + register_bias + key_offset + sequence_semitones
        )

    slots = [
        ChordSlot(symbol=chords_for_bars[min(j, len(chords_for_bars) - 1)], tonic=tonic, mode=mode)
        for j in range(n_bars)
    ]
    q_bars = (n_bars + 1) // 2 if dance_type != "vals" else max(0, n_bars - 3 if n_bars >= 6 else (n_bars + 1) // 2)

    mel_notes, last = generate_phrase_melody(
        rng,
        phrase_bars=n_bars,
        cadence=cadence,
        chords=slots,
        dance_type=dance_type,
        density=density,
        beats_per_bar=float(beats_per_bar),
        prev_end=adjusted_start,
        register_bias=register_bias,
        prefer_contour=prefer or None,
        pitch_cell_intervals=intervals or None,
        rhythm_cells=rhythm_cells,
        pause_frequency=pause_frequency,
        phrase_role_question_bars=q_bars,
    )
    notes = melody_notes_to_dicts(mel_notes, start_bar=start_bar, beats_per_bar=float(beats_per_bar))
    for n in notes:
        n["phrase_bars"] = n_bars
    return notes, int(last)


def _intro_melody(
    rng: random.Random,
    *,
    start_bar: int,
    bars: int,
    beats_per_bar: int,
    tonic: int,
    mode: str,
    chords_for_bars: list[str],
    dance_type: str,
    motif: dict[str, Any] | None = None,
    setup_payoff: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Groove only + tiny pickup — theme has not entered yet.

    E10: when setup lands in intro, plant the home-cell head as anacrusis.
    """
    notes: list[dict[str, Any]] = []
    setup_bar = int((setup_payoff or {}).get("setup_bar", -1))
    plant_setup = (
        motif is not None
        and setup_payoff is not None
        and (setup_payoff.get("setup_section") == "intro")
        and start_bar <= setup_bar < start_bar + bars
    )
    # Last 1–2 bars: short anacrusis into the theme
    for j in range(max(0, bars - 2), bars):
        abs_bar = start_bar + j
        symbol = chords_for_bars[j]
        if plant_setup and abs_bar == setup_bar and motif is not None:
            head_n = 2 if dance_type == "vals" else min(3, max(2, int(motif["n_notes"]) // 2 + 1))
            pitches = _realize_motif(
                rng,
                motif,
                tonic=tonic,
                mode=mode,
                symbol=symbol,
                start_pitch=None,
                transform="prime",
                n=head_n,
                dance_type=dance_type,
            )
            if dance_type == "vals":
                slots = [1.0, 2.0][: len(pitches)] if len(pitches) > 1 else [2.0]
            else:
                start_local = beats_per_bar * 0.25
                slots = list(motif.get("rhythm_question") or [0.0])[: len(pitches)]
                if len(slots) < len(pitches):
                    step = (beats_per_bar - start_local) / max(1, len(pitches))
                    slots = [start_local + i * step for i in range(len(pitches))]
                else:
                    slots = [start_local + (s - slots[0]) for s in slots]
            for i, pitch in enumerate(pitches):
                dur = (
                    (slots[i + 1] - slots[i])
                    if i + 1 < len(slots)
                    else max(0.25, beats_per_bar - slots[i])
                )
                notes.append(
                    {
                        "pitch": int(pitch),
                        "start_beat": round(abs_bar * beats_per_bar + slots[i], 3),
                        "duration_beats": round(max(0.2, dur), 3),
                        "phrase_role": "pickup",
                        "voice": "lead",
                        "motif_role": "setup",
                        "motivic_cell_id": int(setup_payoff.get("cell_id", 0)),
                        "nct": "chord_tone",
                        "structural_weight": 1.0,
                    }
                )
            continue
        chord = _chord_pool(tonic, mode, symbol)
        pitch = rng.choice(chord[1:] or chord)
        start_local = beats_per_bar * 0.5 if dance_type != "vals" else 2.0
        notes.append(
            {
                "pitch": int(pitch),
                "start_beat": round(abs_bar * beats_per_bar + start_local, 3),
                "duration_beats": round(min(0.75, beats_per_bar - start_local), 3),
                "phrase_role": "pickup",
                "voice": "fill",
                "nct": "chord_tone",
                "structural_weight": 0.5,
            }
        )
    # Leave ≥1 beat of air in the intro phrase (call-and-response with LH)
    if notes:
        notes.sort(key=lambda n: n["start_beat"])
        last = notes[-1]
        phrase_end = (start_bar + bars) * beats_per_bar
        end = float(last["start_beat"]) + float(last["duration_beats"])
        if phrase_end - end < 1.0:
            last["duration_beats"] = round(
                max(0.25, phrase_end - 1.0 - float(last["start_beat"])), 3
            )
        # Also ensure gap between consecutive intro notes when multiple
        for i in range(len(notes) - 1):
            a, b = notes[i], notes[i + 1]
            a_end = float(a["start_beat"]) + float(a["duration_beats"])
            if float(b["start_beat"]) - a_end < 0.05:
                a["duration_beats"] = round(
                    max(0.2, float(b["start_beat"]) - float(a["start_beat"]) - 0.05), 3
                )
    return notes


def _bridge_melody(
    rng: random.Random,
    *,
    start_bar: int,
    bars: int,
    beats_per_bar: int,
    tonic: int,
    mode: str,
    chords_for_bars: list[str],
) -> list[dict[str, Any]]:
    """Sparse rising line / silence — clears space before next theme entry."""
    notes: list[dict[str, Any]] = []
    for j in range(bars):
        if j % 2 == 1 and bars > 2:
            continue  # leave air
        symbol = chords_for_bars[j]
        chord = _chord_pool(tonic, mode, symbol)
        pitch = _clamp_melody(chord[-1] + (2 if j == bars - 1 else 0))
        notes.append(
            {
                "pitch": int(pitch),
                "start_beat": round((start_bar + j) * beats_per_bar, 3),
                "duration_beats": round(beats_per_bar * 0.9, 3),
                "phrase_role": "bridge",
                "voice": "lead",
                "phrase_end": j == bars - 1,
                "nct": "chord_tone",
                "structural_weight": 1.0,
            }
        )
    # Ensure ≥1 beat rest inside the bridge phrase
    if notes:
        notes.sort(key=lambda n: n["start_beat"])
        # Shorten last note / leave air mid-bridge
        mid = notes[len(notes) // 2]
        mid["duration_beats"] = round(min(float(mid["duration_beats"]), 0.75), 3)
        last = notes[-1]
        phrase_end = (start_bar + bars) * beats_per_bar
        if phrase_end - (float(last["start_beat"]) + float(last["duration_beats"])) < 1.0:
            last["duration_beats"] = round(
                max(0.35, phrase_end - 1.0 - float(last["start_beat"])), 3
            )
    return notes


def _coda_melody(
    rng: random.Random,
    *,
    start_bar: int,
    bars: int,
    beats_per_bar: int,
    tonic: int,
    mode: str,
    chords_for_bars: list[str],
    theme_cells: list[list[int]] | None,
    dance_type: str,
    motif: dict[str, Any] | None = None,
    quote_motif: dict[str, Any] | None = None,
) -> tuple[list[dict[str, Any]], set[int]]:
    """Theme tag (if we have one) then a long tonic cadence."""
    notes: list[dict[str, Any]] = []
    interweave_bars: set[int] = set()
    tag_bars = min(2, bars - 1) if bars > 1 else 0
    quote = quote_motif if quote_motif is not None and quote_motif is not motif else None
    lead_motif = quote or motif
    if lead_motif and tag_bars:
        for j in range(tag_bars):
            symbol = chords_for_bars[j]
            use = quote if (quote is not None and j == 0) else (motif or lead_motif)
            if use is quote and quote is not None:
                interweave_bars.add(start_bar + j)
            pitches = _realize_motif(
                rng,
                use,
                tonic=tonic,
                mode=mode,
                symbol=symbol,
                start_pitch=None,
                transform="prime" if j == 0 else "answer",
                n=min(3, int(use["n_notes"])),
                dance_type=dance_type,
            )
            notes.extend(
                _emit_bar_notes(
                    rng,
                    bar=start_bar + j,
                    beats_per_bar=beats_per_bar,
                    pitches=pitches,
                    density="low",
                    variation="low",
                    phrase_end=j == tag_bars - 1,
                    role="answer" if j == tag_bars - 1 else "question",
                    dance_type=dance_type,
                    voice="lead",
                    tonic=tonic,
                    mode=mode,
                    symbol=symbol,
                    fixed_placements=list(use["rhythm_question" if j == 0 else "rhythm_answer"]),
                )
            )
    elif theme_cells and tag_bars:
        for j in range(tag_bars):
            cell = theme_cells[j % len(theme_cells)]
            symbol = chords_for_bars[j]
            pitches = [
                _nearest(_chord_pool(tonic, mode, symbol), p) for p in cell[:2]
            ]
            notes.extend(
                _emit_bar_notes(
                    rng,
                    bar=start_bar + j,
                    beats_per_bar=beats_per_bar,
                    pitches=pitches,
                    density="low",
                    variation="low",
                    phrase_end=j == tag_bars - 1,
                    role="answer" if j == tag_bars - 1 else "question",
                    dance_type=dance_type,
                    voice="lead",
                    tonic=tonic,
                    mode=mode,
                    symbol=symbol,
                )
            )
    # Final cadence note on tonic
    last = bars - 1
    tonic_pitch = _clamp_melody(_chord_pool(tonic, mode, chords_for_bars[last])[0])
    notes.append(
        {
            "pitch": int(tonic_pitch),
            "start_beat": round((start_bar + last) * beats_per_bar, 3),
            "duration_beats": round(beats_per_bar * 1.5, 3),
            "phrase_role": "cadence",
            "voice": "lead",
            "phrase_end": True,
            "nct": "chord_tone",
            "structural_weight": 1.0,
        }
    )
    return notes, interweave_bars


def _annotate_drama(
    notes: list[dict[str, Any]],
    drama: dict[str, Any],
) -> list[dict[str, Any]]:
    pause = set(drama.get("pause_bars") or [])
    energy = drama.get("energy") or {}
    out: list[dict[str, Any]] = []
    for n in notes:
        bpb = int(n.pop("_bpb", 2)) or 2
        bar = int(float(n["start_beat"]) // bpb)
        if bar in pause and n.get("voice") == "lead":
            continue  # dramatic hole — drop lead note
        tag = _drama_tag_for_bar(bar, drama)
        n["drama"] = tag
        # Sustain into the peak; don't chop anticipation into dust
        if tag == "anticipate":
            n["duration_beats"] = round(float(n["duration_beats"]) * 1.2, 3)
        elif tag == "climax":
            n["duration_beats"] = round(float(n["duration_beats"]) * 1.12, 3)
        elif tag == "rise":
            n["duration_beats"] = round(float(n["duration_beats"]) * 1.05, 3)
        n["energy"] = energy.get(bar, 0.5)
        out.append(n)
    return out


def _melody_for_section(
    rng: random.Random,
    *,
    start_bar: int,
    bars: int,
    beats_per_bar: int,
    tonic: int,
    mode: str,
    chords_for_bars: list[str],
    density: Level,
    variation: Level,
    section_name: str,
    dance_type: str = "tango",
    theme_state: dict[str, Any] | None = None,
    drama: dict[str, Any] | None = None,
    form_phrases: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    theme_state = theme_state if theme_state is not None else {}
    drama = drama or {}
    pause = set(drama.get("pause_bars") or [])
    pause_frequency = str(theme_state.get("pause_frequency") or "medium")
    rhythm_cells = theme_state.get("rhythm_cells")

    cells: list[dict[str, Any]] = list(theme_state.get("motivic_cells") or [])
    if not cells and theme_state.get("motif"):
        cells = [theme_state["motif"]]
    n_cells = len(cells)
    cell_id = _motivic_cell_index_for_section(section_name, n_cells) if n_cells else 0
    primary_motif: dict[str, Any] | None = cells[cell_id] if cells else theme_state.get("motif")
    quote_motif = cells[0] if n_cells >= 2 and cell_id != 0 else None
    interweave_bars: set[int] = set()
    setup_payoff: dict[str, Any] = dict(theme_state.get("setup_payoff") or {})
    home_motif: dict[str, Any] | None = cells[0] if cells else primary_motif
    home_tonic = int(theme_state.get("home_tonic") or tonic)
    key_offset = int(tonic) - home_tonic

    def _finish(raw: list[dict[str, Any]], extra_iw: set[int] | None = None) -> list[dict[str, Any]]:
        for n in raw:
            n["_bpb"] = beats_per_bar
            n.setdefault("nct", "chord_tone")
            n.setdefault("structural_weight", 0.0)
            n["pitch"] = int(_clamp_melody(int(n["pitch"])))
        annotated = _annotate_drama(raw, drama)
        return _stamp_motivic_meta(
            annotated,
            section_name=section_name,
            start_bar=start_bar,
            section_bars=bars,
            beats_per_bar=beats_per_bar,
            cell_id=cell_id if n_cells else None,
            drama=drama,
            interweave_bars=(interweave_bars | (extra_iw or set())),
        )

    if section_name == "intro":
        notes = _intro_melody(
            rng,
            start_bar=start_bar,
            bars=bars,
            beats_per_bar=beats_per_bar,
            tonic=tonic,
            mode=mode,
            chords_for_bars=chords_for_bars,
            dance_type=dance_type,
            motif=home_motif,
            setup_payoff=setup_payoff or None,
        )
        return _finish(notes)
    if section_name == "bridge":
        notes = _bridge_melody(
            rng,
            start_bar=start_bar,
            bars=bars,
            beats_per_bar=beats_per_bar,
            tonic=tonic,
            mode=mode,
            chords_for_bars=chords_for_bars,
        )
        if quote_motif is not None:
            # Quote home cell on the last sounding bar (non-primary cell section)
            interweave_bars.add(start_bar + bars - 1)
            if notes:
                symbol = chords_for_bars[-1]
                quoted = _realize_motif(
                    rng,
                    quote_motif,
                    tonic=tonic,
                    mode=mode,
                    symbol=symbol,
                    start_pitch=None,
                    transform="prime",
                    n=min(3, int(quote_motif["n_notes"])),
                    dance_type=dance_type,
                )
                if quoted:
                    notes[-1]["pitch"] = int(quoted[0])
        return _finish(notes)
    if section_name == "coda":
        notes, coda_iw = _coda_melody(
            rng,
            start_bar=start_bar,
            bars=bars,
            beats_per_bar=beats_per_bar,
            tonic=tonic,
            mode=mode,
            chords_for_bars=chords_for_bars,
            theme_cells=theme_state.get("cells"),
            dance_type=dance_type,
            motif=primary_motif if setup_payoff.get("payoff_section") != "coda" else home_motif,
            quote_motif=quote_motif,
        )
        payoff_bar = int(setup_payoff.get("payoff_bar", -1))
        if setup_payoff.get("payoff_section") == "coda":
            for n in notes:
                bar = int(float(n["start_beat"]) // max(beats_per_bar, 1))
                if bar == payoff_bar:
                    n["motif_role"] = "payoff"
        return _finish(notes, coda_iw)

    notes_per_bar = DENSITY_NOTES_PER_BAR.get(dance_type, DENSITY_NOTES_PER_BAR["tango"])[
        density
    ]
    var = VARIATION_STRENGTH[variation]
    if dance_type == "tango" and var >= 0.5 and rng.random() < var * 0.25:
        notes_per_bar = min(beats_per_bar * 4, notes_per_bar + 1)

    motif: dict[str, Any] | None = primary_motif
    if motif is None:
        motif = _roll_piece_motif(rng, dance_type=dance_type, tonic=tonic, mode=mode)
        theme_state["motif"] = motif
        if not cells:
            theme_state["motivic_cells"] = [motif]
            cells = [motif]
            n_cells = 1
            cell_id = 0

    notes: list[dict[str, Any]] = []
    last_pitch: int | None = None
    phrase_i = 0
    seq_unit = int(motif.get("sequence_interval") or 0)

    phrases = _partition_phrases(
        bars=bars,
        start_bar=start_bar,
        chords_for_bars=chords_for_bars,
        pause=pause,
        dance_type=dance_type,
    )
    # Prefer M2 form phrase boundaries when they cover this section
    form_phrase_cadence: dict[tuple[int, int], str] = {}
    if form_phrases:
        mapped: list[tuple[int, int]] = []
        for fp in form_phrases:
            bf = int(fp["bar_from"]) - 1  # to 0-based absolute
            pb = int(fp["bars"])
            local = bf - start_bar
            if local < 0 or local >= bars:
                continue
            plen = min(pb, bars - local)
            mapped.append((local, plen))
            form_phrase_cadence[(local, plen)] = str(fp.get("cadence") or "authentic")
        if mapped and sum(p for _, p in mapped) >= bars - 1:
            phrases = mapped

    prev_dens: Level = density
    for local_start, plen in phrases:
        abs_start = start_bar + local_start
        tags = [_drama_tag_for_bar(abs_start + k, drama) for k in range(plen)]
        if "climax" in tags:
            tag = "climax"
        elif "anticipate" in tags:
            tag = "anticipate"
        elif "rise" in tags:
            tag = "rise"
        else:
            tag = tags[0] if tags else "normal"
        local_density = _density_for_drama(density, tag, dance_type=dance_type)
        energy0 = float((drama.get("energy") or {}).get(abs_start, 0.5))
        dev = _motivic_development_level(
            local_bar=local_start,
            section_bars=bars,
            drama_tag=tag,
            energy=energy0,
            section_name=section_name,
        )
        local_density = _density_for_development(local_density, dev, dance_type=dance_type)
        local_density = _step_density(prev_dens, local_density)
        prev_dens = local_density
        reg = _register_for_drama(tag, phrase_i)
        if reg == 0:
            reg = _phrase_register_bias(
                rng,
                section_name=section_name,
                role="question",
                drama_high=False,
                variation=var,
            )

        phrase_motif = motif
        seq = 0
        transform_q: Literal["prime", "invert", "answer", "sequence"] = "prime"
        payoff_bar = int(setup_payoff.get("payoff_bar", -1))
        setup_bar = int(setup_payoff.get("setup_bar", -1))
        phrase_covers_payoff = abs_start <= payoff_bar < abs_start + plen
        phrase_covers_setup = (
            section_name == "A"
            and setup_payoff.get("setup_section") == "A"
            and abs_start <= setup_bar < abs_start + plen
        )

        if phrase_covers_payoff and home_motif is not None:
            # E10: scheduled recall — clear home cell at the planned anchor
            phrase_motif = home_motif
            pt = str(setup_payoff.get("payoff_transform") or "prime")
            transform_q = "sequence" if pt == "sequence" else "prime"
            seq = seq_unit if transform_q == "sequence" else 0
            if reg == 0:
                reg = 12 if section_name == "A_prime" else 7
            for k in range(plen):
                interweave_bars.add(abs_start + k)
        elif (
            quote_motif is not None
            and section_name == "B"
            and phrase_i % 2 == 1
        ):
            phrase_motif = quote_motif
            transform_q = "prime"
            for k in range(plen):
                interweave_bars.add(abs_start + k)
        elif section_name == "B":
            seq = seq_unit * (1 + phrase_i // 2)
            transform_q = "invert" if phrase_i % 2 else "sequence"
        elif section_name == "A_prime":
            seq = seq_unit if phrase_i >= 2 else 0
            transform_q = "prime"
            # Recap: lift register more often so A′ reads as the same tune, brighter
            if reg == 0 and rng.random() < 0.65:
                reg = 12
            elif reg == 0:
                reg = 7 if rng.random() < 0.45 else 0
        else:
            seq = seq_unit * (phrase_i // 3)
            transform_q = "prime"

        chord_slice = chords_for_bars[local_start : local_start + plen]
        cadence = form_phrase_cadence.get(
            (local_start, plen),
            "authentic" if local_start + plen >= bars else "half",
        )
        emitted, last_pitch = _emit_phrase(
            rng,
            start_bar=abs_start,
            n_bars=plen,
            beats_per_bar=beats_per_bar,
            chords_for_bars=chord_slice,
            motif=phrase_motif,
            density=local_density,
            variation=variation,
            dance_type=dance_type,
            tonic=tonic,
            mode=mode,
            transform_q=transform_q,
            register_bias=reg,
            sequence_semitones=seq,
            start_pitch=last_pitch if phrase_i > 0 else None,
            key_offset=key_offset,
            cadence=cadence,
            rhythm_cells=rhythm_cells,
            pause_frequency=pause_frequency,
        )
        if phrase_covers_payoff:
            for n in emitted:
                n["motif_role"] = "payoff"
        elif phrase_covers_setup:
            for n in emitted:
                n["motif_role"] = "setup"
        notes.extend(emitted)
        if section_name == "A" and phrase_i == 0:
            # Snapshot first phrase contour for coda fallback
            lead_ps = [n["pitch"] for n in emitted if n.get("voice") == "lead"]
            mid = max(1, len(lead_ps) // 2)
            theme_state["cells"] = [lead_ps[:mid], lead_ps[mid:] or lead_ps[-2:]]
        phrase_i += 1

    return _finish(notes)


def build_skeleton(
    *,
    dance_type: str = "tango",
    key: str | None = None,
    progression_id: str | None = "random",
    form_id: str | None = "golden_age_short",
    melody_density: Level = "medium",
    melody_variation: Level = "medium",
    seed: int | None = None,
) -> dict[str, Any]:
    seed = int(seed if seed is not None else random.randint(1, 2_147_483_647))
    rng = random.Random(seed)

    if melody_density not in ("low", "medium", "high"):
        raise ValueError("melody_density must be low|medium|high")
    if melody_variation not in VARIATION_STRENGTH:
        raise ValueError("melody_variation must be low|medium|high")

    if dance_type not in DANCE_TYPES:
        raise ValueError(f"Unknown dance_type: {dance_type}")
    dance = DANCE_TYPES[dance_type]
    beats_per_bar = dance["time_signature"][0]

    if key in (None, "", "random"):
        prog_mode = _progression_mode_for_id(str(progression_id or ""))
        if prog_mode == "major":
            pool = KEYS_MAJOR
        elif prog_mode == "minor":
            pool = KEYS_MINOR
        else:
            bias = dance.get("key_bias", "minor")
            if bias == "major":
                pool = KEYS_MAJOR * 3 + KEYS_MINOR  # prefer major for milonga/vals
            elif bias == "minor":
                pool = KEYS_MINOR * 3 + KEYS_MAJOR
            else:
                pool = KEYS
        key_name, mode, tonic = _parse_key(rng.choice(pool))
    else:
        key_name, mode, tonic = _parse_key(key)

    if form_id in (None, "", "random"):
        form_id = rng.choice(list(FORMS.keys()))
    if form_id not in FORMS:
        raise ValueError(f"Unknown form_id: {form_id}")
    form_def = FORMS[form_id]
    sections = form_def["sections"]
    total_bars = sum(b for _, b in sections)

    user_locked_progression = bool(
        progression_id and progression_id not in (None, "", "random")
    )
    home_prog_id, home_progression = pick_progression(rng, mode, progression_id)
    bars_per_chord = int(dance["bars_per_chord"])
    # Extra harmonic-rhythm variation (tango often flips between 1–2 bars/chord)
    if (
        dance_type == "tango"
        and not user_locked_progression
        and rng.random() < VARIATION_STRENGTH[melody_variation] * 0.45
    ):
        bars_per_chord = 1 if bars_per_chord == 2 else 2

    drama = _build_drama_map(
        rng, sections, dance_type=dance_type, variation=melody_variation
    )

    chords: list[dict[str, Any]] = []
    melody: list[dict[str, Any]] = []
    form_labels: list[str] = []
    harmony_plan: list[dict[str, Any]] = []
    piece_harmony: dict[str, Any] = {}
    theme_state: dict[str, Any] = {}
    cells = _roll_motivic_cells(rng, dance_type, tonic, mode)
    rhythm_cells, _pitch_cells = sample_piece_cells(rng, dance_type)
    theme_state["motivic_cells"] = cells
    theme_state["motif"] = cells[0]
    theme_state["rhythm_cells"] = rhythm_cells
    theme_state["home_tonic"] = tonic
    theme_state["home_mode"] = mode
    theme_state["home_key"] = key_name
    # Di Sarli-ish pause bias when variation high (style still render-side; skeleton rests)
    theme_state["pause_frequency"] = (
        "high" if melody_variation == "high" and rng.random() < 0.35 else "medium"
    )
    climax0 = int((drama.get("climax_bars") or [0])[0])
    setup_payoff = _plan_motif_setup_payoff(
        rng, sections, climax_bar=climax0, n_cells=len(cells)
    )
    theme_state["setup_payoff"] = setup_payoff
    section_groove = _roll_section_groove(rng, dance_type)
    # JSON-friendly (tuples → lists)
    section_groove = {
        name: {
            **intent,
            "colour_slots": list(intent.get("colour_slots") or ()),
        }
        for name, intent in section_groove.items()
    }
    bar = 0

    for section_name, section_bars in sections:
        form_labels.append(section_name)
        sec = plan_section_harmony(
            rng,
            section_name=section_name,
            home_key=key_name,
            home_mode=mode,
            home_tonic=tonic,
            home_prog_id=home_prog_id,
            home_progression=home_progression,
            user_locked_progression=user_locked_progression,
            piece_harmony=piece_harmony,
        )
        harmony_plan.append(sec)

        section_start_bar = bar
        pause = set(drama.get("pause_bars") or [])
        section_symbols, cadence_roles, phrase_objs = build_section_harmony(
            rng,
            section_name=section_name,
            section_bars=section_bars,
            section_start_bar=section_start_bar,
            dance_type=dance_type,
            sec=sec,
            pause_bars=pause,
        )

        elaboration: dict[str, Any] | None = None
        if section_name in ("A_prime", "variacion"):
            elaboration = _roll_a_prime_elaboration(rng, melody_variation)
            sec["elaboration"] = elaboration

        base_groove = section_groove.get(section_name) or {
            "groove_role": "home",
            "colour_slots": [],
            "lh": "steady",
            "force_primary": False,
        }

        for j in range(section_bars):
            symbol = section_symbols[j]
            energy = float((drama.get("energy") or {}).get(bar, 0.5))
            tag = _drama_tag_for_bar(bar, drama)
            # Per-bar groove intent: role + local index for continuous run execution
            groove = {
                **base_groove,
                "section_local_bar": j,
                "section_bars": section_bars,
            }
            entry: dict[str, Any] = {
                "bar": bar,
                "symbol": symbol,
                "start_beat": bar * beats_per_bar,
                "duration_beats": beats_per_bar,
                "key": sec["key"],
                "mode": sec["mode"],
                "tonic": sec["tonic"],
                "section": section_name,
                "drama": tag,
                "energy": energy,
                "groove": groove,
            }
            role = cadence_roles.get(j)
            if role:
                entry["cadence"] = role
            if elaboration:
                entry["elaboration"] = elaboration
            chords.append(entry)
            bar += 1

        sec["bar_from"] = section_start_bar + 1
        sec["bar_to"] = bar
        sec["progression_template"] = list(section_symbols)
        sec["bars_per_chord"] = 1
        sec["phrases"] = [phrase_to_dict(p) for p in phrase_objs]

        dens: Level = melody_density
        if section_name == "B" and melody_density == "high":
            dens = "medium"
        elif section_name in ("A_prime", "variacion") and elaboration and elaboration.get("density_bump"):
            dens = _LEVEL_UP[melody_density]

        melody.extend(
            _melody_for_section(
                rng,
                start_bar=section_start_bar,
                bars=section_bars,
                beats_per_bar=beats_per_bar,
                tonic=int(sec["tonic"]),
                mode=str(sec["mode"]),
                chords_for_bars=section_symbols,
                density=dens,
                variation=melody_variation,
                section_name=section_name,
                dance_type=dance_type,
                theme_state=theme_state,
                drama=drama,
                form_phrases=[phrase_to_dict(p) for p in phrase_objs],
            )
        )

    return {
        "seed": seed,
        "dance_type": dance_type,
        "key": key_name,
        "mode": mode,
        "tonic": tonic,
        "time_signature": list(dance["time_signature"]),
        "beats_per_bar": beats_per_bar,
        "default_bpm": dance["default_bpm"],
        "default_rhythm": dance.get("default_rhythm"),
        "form_id": form_id,
        "form": form_labels,
        "progression_id": home_prog_id,
        "progression": home_progression,
        "harmony_plan": harmony_plan,
        "drama": {
            "climax_bars": [b + 1 for b in drama["climax_bars"]],
            "pause_bars": [b + 1 for b in drama["pause_bars"]],
            "dense_bars": [b + 1 for b in drama["dense_bars"]],
            "rise_bars": [b + 1 for b in drama.get("rise_bars", [])],
            "anticipate_bars": [b + 1 for b in drama.get("anticipate_bars", [])],
            "release_bars": [b + 1 for b in drama.get("release_bars", [])],
        },
        "structural_anchors": {
            k: int(v) + 1
            for k, v in (drama.get("anchors") or {}).items()
        },
        "motif_setup_payoff": {
            **{k: v for k, v in setup_payoff.items() if k not in ("setup_bar", "payoff_bar")},
            "setup_bar": int(setup_payoff["setup_bar"]) + 1,
            "payoff_bar": int(setup_payoff["payoff_bar"]) + 1,
        },
        "section_groove": section_groove,
        "melody_density": melody_density,
        "melody_variation": melody_variation,
        "bars": total_bars,
        "chords": chords,
        "melody": melody,
        "motif": _export_motivic_cell(theme_state.get("motif") or {}),
        "motivic_cells": [_export_motivic_cell(c) for c in (theme_state.get("motivic_cells") or [])],
        "motivic_section_map": {
            name: _motivic_cell_index_for_section(
                name, len(theme_state.get("motivic_cells") or [])
            )
            for name in dict.fromkeys(form_labels)
        },
        "tension_curve": [
            round(float((drama.get("energy") or {}).get(i, 0.5)), 3)
            for i in range(total_bars)
        ],
    }
