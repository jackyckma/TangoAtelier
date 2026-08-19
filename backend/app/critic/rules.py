"""Hard-rule musicality checks (measurement only — no engine fixes)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.critic.chord_vocab import expected_pitch_classes
from app.engine.harmony import chord_pitches
from app.engine.skeleton import DENSITY_NOTES_PER_BAR, MELODY_HI, MELODY_LO

LH_LO = 28
LH_HI = 60

SECTION_CADENCE_NAMES = frozenset({"A", "B", "A_prime"})
AUTHENTIC_SYMBOLS = frozenset({"i", "I"})
HALF_SYMBOLS = frozenset({"V", "V7", "V7b9"})
VALID_SECTION_END = AUTHENTIC_SYMBOLS | HALF_SYMBOLS
PHRASE_CADENCE_SYMBOLS = VALID_SECTION_END | frozenset({"VI", "vi"})

LEAP_RECOVERY_ALLOWANCE = 0.20


@dataclass
class Violation:
    rule_id: str
    severity: str
    bar: int | None
    detail: str


def _lead_notes(skeleton: dict[str, Any]) -> list[dict[str, Any]]:
    notes = skeleton.get("melody") or []
    lead = [n for n in notes if n.get("voice", "lead") == "lead"]
    return sorted(lead if lead else notes, key=lambda n: float(n["start_beat"]))


def _is_tonic(symbol: str) -> bool:
    return symbol in AUTHENTIC_SYMBOLS


def _is_dominant(symbol: str) -> bool:
    return symbol in HALF_SYMBOLS


def _check_chord_spelling(skeleton: dict[str, Any]) -> list[Violation]:
    out: list[Violation] = []
    for ch in skeleton.get("chords") or []:
        symbol = str(ch["symbol"])
        tonic = int(ch["tonic"])
        mode = str(ch["mode"])
        expected = expected_pitch_classes(tonic, mode, symbol)
        if expected is None:
            continue
        actual = frozenset(p % 12 for p in chord_pitches(tonic, mode, symbol))
        if actual != expected:
            bar = int(ch["bar"]) + 1
            out.append(
                Violation(
                    rule_id="CHORD_SPELLING_INVALID",
                    severity="error",
                    bar=bar,
                    detail=(
                        f"{symbol} in {ch.get('key')} spells PCs {sorted(actual)}; "
                        f"expected {sorted(expected)}"
                    ),
                )
            )
    return out


def _section_chords(skeleton: dict[str, Any], section_name: str) -> list[dict[str, Any]]:
    return [c for c in skeleton.get("chords") or [] if str(c.get("section")) == section_name]


def _check_section_no_cadence(skeleton: dict[str, Any]) -> list[Violation]:
    out: list[Violation] = []
    for section in SECTION_CADENCE_NAMES:
        chords = _section_chords(skeleton, section)
        if not chords:
            continue
        last = chords[-1]
        sym = str(last["symbol"])
        if sym not in VALID_SECTION_END:
            out.append(
                Violation(
                    rule_id="SECTION_NO_CADENCE",
                    severity="error",
                    bar=int(last["bar"]) + 1,
                    detail=f"Section {section} ends on {sym}, not i/I/V/V7",
                )
            )
    return out


def _check_phrase_no_cadence(skeleton: dict[str, Any]) -> list[Violation]:
    out: list[Violation] = []
    bpb = int(skeleton.get("beats_per_bar") or 2)
    chord_by_bar = {int(c["bar"]): c for c in skeleton.get("chords") or []}

    for sec in skeleton.get("harmony_plan") or []:
        for phrase in sec.get("phrases") or []:
            bar_from = int(phrase["bar_from"])  # 1-based
            bars = int(phrase["bars"])
            end_bar_0 = bar_from - 1 + bars - 1
            ch = chord_by_bar.get(end_bar_0)
            if ch is None:
                continue
            sym = str(ch["symbol"])
            if sym not in PHRASE_CADENCE_SYMBOLS:
                out.append(
                    Violation(
                        rule_id="PHRASE_NO_CADENCE",
                        severity="warning",
                        bar=end_bar_0 + 1,
                        detail=f"Phrase ending in {sec.get('section')} on {sym}",
                    )
                )
            elif sym in PHRASE_CADENCE_SYMBOLS - VALID_SECTION_END:
                cadence = ch.get("cadence")
                if cadence not in ("authentic", "half", "approach", "deceptive"):
                    out.append(
                        Violation(
                            rule_id="PHRASE_NO_CADENCE",
                            severity="warning",
                            bar=end_bar_0 + 1,
                            detail=f"Phrase ends on colour chord {sym} without cadence role",
                        )
                    )
    return out


def _check_leap_not_recovered(skeleton: dict[str, Any]) -> list[Violation]:
    notes = _lead_notes(skeleton)
    if len(notes) < 3:
        return []
    violations: list[Violation] = []
    leaps = 0
    bpb = float(skeleton.get("beats_per_bar") or 2)
    for i in range(len(notes) - 2):
        a, b, c = notes[i], notes[i + 1], notes[i + 2]
        iv = int(b["pitch"]) - int(a["pitch"])
        if abs(iv) < 5:
            continue
        leaps += 1
        step = int(c["pitch"]) - int(b["pitch"])
        unrecovered = (iv > 0 and step >= 0) or (iv < 0 and step <= 0)
        if not unrecovered:
            continue
        bar = int(float(b["start_beat"]) // bpb) + 1
        direction = "downward" if iv > 0 else "upward"
        violations.append(
            Violation(
                rule_id="LEAP_NOT_RECOVERED",
                severity="warning",
                bar=bar,
                detail=(
                    f"Leap {iv:+d} semitones not followed by {direction} step "
                    f"(next step {step:+d})"
                ),
            )
        )
    if leaps and len(violations) / leaps <= LEAP_RECOVERY_ALLOWANCE:
        return []
    return violations


def _check_melody_no_long_note(skeleton: dict[str, Any]) -> list[Violation]:
    bpb = float(skeleton.get("beats_per_bar") or 2)
    total_bars = int(skeleton.get("bars") or 0)
    notes = _lead_notes(skeleton)
    out: list[Violation] = []
    window = 8
    for start in range(0, max(total_bars, 1), window):
        end_beat = (start + window) * bpb
        start_beat = start * bpb
        window_notes = [
            n
            for n in notes
            if start_beat <= float(n["start_beat"]) < end_beat
        ]
        has_long = any(float(n["duration_beats"]) >= 1.5 for n in window_notes)
        if window_notes and not has_long:
            out.append(
                Violation(
                    rule_id="MELODY_NO_LONG_NOTE",
                    severity="warning",
                    bar=start + 1,
                    detail=f"No melody note ≥1.5 beats in bars {start + 1}–{min(start + window, total_bars)}",
                )
            )
    return out


def _check_melody_no_rest(skeleton: dict[str, Any]) -> list[Violation]:
    bpb = float(skeleton.get("beats_per_bar") or 2)
    notes = _lead_notes(skeleton)
    out: list[Violation] = []

    for sec in skeleton.get("harmony_plan") or []:
        for phrase in sec.get("phrases") or []:
            bar_from = int(phrase["bar_from"])
            bars = int(phrase["bars"])
            start_beat = (bar_from - 1) * bpb
            end_beat = start_beat + bars * bpb
            phrase_notes = [
                n
                for n in notes
                if start_beat <= float(n["start_beat"]) < end_beat
            ]
            if not phrase_notes:
                out.append(
                    Violation(
                        rule_id="MELODY_NO_REST",
                        severity="warning",
                        bar=bar_from,
                        detail=f"Phrase in {sec.get('section')} has no melody (implicit rest)",
                    )
                )
                continue
            # gaps ≥1 beat between consecutive notes or after last note
            times = sorted(float(n["start_beat"]) for n in phrase_notes)
            durs = {float(n["start_beat"]): float(n["duration_beats"]) for n in phrase_notes}
            has_rest = False
            for i, t in enumerate(times):
                end = t + durs[t]
                next_start = times[i + 1] if i + 1 < len(times) else end_beat
                gap = next_start - end
                if gap >= 1.0:
                    has_rest = True
                    break
            if not has_rest:
                out.append(
                    Violation(
                        rule_id="MELODY_NO_REST",
                        severity="warning",
                        bar=bar_from,
                        detail=f"No rest ≥1 beat in {sec.get('section')} phrase ({bars} bars)",
                    )
                )
    return out


def _lh_block_voices(rendered: dict[str, Any], skeleton: dict[str, Any]) -> list[tuple[float, int, int]]:
    """Return (start_time, bass_pitch, top_pitch) for each LH block attack."""
    bpm = float(rendered.get("bpm") or skeleton.get("default_bpm") or 64)
    bpb = float(skeleton.get("beats_per_bar") or 2)
    bar_len = bpb * (60.0 / bpm)
    lh = [n for n in rendered.get("notes") or [] if n.get("track") == "piano_lh"]
    groups: dict[tuple[int, float], list[int]] = {}
    for n in lh:
        start = float(n["start"])
        bar = int(start / bar_len) if bar_len > 0 else 0
        key = (bar, round(start, 4))
        groups.setdefault(key, []).append(int(n["pitch"]))
    blocks: list[tuple[float, int, int]] = []
    for (bar, start), pitches in sorted(groups.items(), key=lambda x: x[0][1]):
        if len(pitches) < 2:
            continue
        blocks.append((start, min(pitches), max(pitches)))
    return blocks


def _check_lh_parallel_fifths(
    skeleton: dict[str, Any], rendered: dict[str, Any]
) -> list[Violation]:
    blocks = _lh_block_voices(rendered, skeleton)
    out: list[Violation] = []
    for (prev_start, pb, pt), (curr_start, cb, ct) in zip(blocks, blocks[1:]):
        bass_move = cb - pb
        top_move = ct - pt
        if bass_move == 0 or top_move == 0:
            continue
        if (bass_move > 0) != (top_move > 0):
            continue
        if abs(bass_move - top_move) <= 1:
            interval = abs(top_move)
            if interval in (7, 12) or abs(interval - 7) <= 1:
                bpb = float(skeleton.get("beats_per_bar") or 2)
                bpm = float(rendered.get("bpm") or 64)
                bar_len = bpb * (60.0 / bpm)
                bar = int(curr_start / bar_len) + 1 if bar_len else None
                out.append(
                    Violation(
                        rule_id="LH_PARALLEL_FIFTHS",
                        severity="warning",
                        bar=bar,
                        detail=f"Parallel outer voices moved {bass_move} semitones (P5/P8 motion)",
                    )
                )
    return out


def _check_range_exceeded(
    skeleton: dict[str, Any], rendered: dict[str, Any] | None
) -> list[Violation]:
    out: list[Violation] = []
    bpb = float(skeleton.get("beats_per_bar") or 2)
    for n in _lead_notes(skeleton):
        p = int(n["pitch"])
        if p < MELODY_LO or p > MELODY_HI:
            bar = int(float(n["start_beat"]) // bpb) + 1
            out.append(
                Violation(
                    rule_id="RANGE_EXCEEDED",
                    severity="error",
                    bar=bar,
                    detail=f"Melody pitch {p} outside {MELODY_LO}..{MELODY_HI}",
                )
            )
    if rendered:
        for n in rendered.get("notes") or []:
            if n.get("track") != "piano_lh":
                continue
            p = int(n["pitch"])
            if p < LH_LO or p > LH_HI:
                bpm = float(rendered.get("bpm") or 64)
                bar_len = bpb * (60.0 / bpm)
                bar = int(float(n["start"]) / bar_len) + 1 if bar_len else None
                out.append(
                    Violation(
                        rule_id="RANGE_EXCEEDED",
                        severity="error",
                        bar=bar,
                        detail=f"LH pitch {p} outside {LH_LO}..{LH_HI}",
                    )
                )
    return out


def _check_density_mismatch(skeleton: dict[str, Any]) -> list[Violation]:
    dance = str(skeleton.get("dance_type") or "tango")
    density = str(skeleton.get("melody_density") or "medium")
    target = float(DENSITY_NOTES_PER_BAR.get(dance, {}).get(density, 5))
    bpb = float(skeleton.get("beats_per_bar") or 2)
    total_bars = int(skeleton.get("bars") or 0)
    if total_bars <= 0:
        return []
    notes = _lead_notes(skeleton)
    actual = len(notes) / total_bars
    if target <= 0:
        return []
    deviation = abs(actual - target) / target
    if deviation > 0.40:
        return [
            Violation(
                rule_id="DENSITY_MISMATCH",
                severity="error",
                bar=None,
                detail=(
                    f"Lead notes/bar {actual:.2f} vs target {target:.1f} "
                    f"({deviation * 100:.0f}% off, dance={dance} density={density})"
                ),
            )
        ]
    return []


def _check_harmonic_rhythm_orphan(skeleton: dict[str, Any]) -> list[Violation]:
    out: list[Violation] = []
    default_bpc = 2
    dance = skeleton.get("dance_type")
    if dance:
        from app.engine.catalog import DANCE_TYPES

        default_bpc = int(DANCE_TYPES.get(str(dance), {}).get("bars_per_chord") or 2)

    for sec in skeleton.get("harmony_plan") or []:
        section_name = str(sec.get("section") or "")
        if section_name in ("intro", "bridge", "coda"):
            continue
        prog = sec.get("progression_template") or sec.get("progression") or []
        if not prog:
            continue
        bpc = int(sec.get("bars_per_chord") or default_bpc)
        cycle = len(prog) * bpc
        bar_from = int(sec.get("bar_from") or 1)
        bar_to = int(sec.get("bar_to") or bar_from)
        section_bars = bar_to - bar_from
        if cycle <= 0:
            continue
        if section_bars % cycle != 0:
            out.append(
                Violation(
                    rule_id="HARMONIC_RHYTHM_ORPHAN",
                    severity="warning",
                    bar=bar_to,
                    detail=(
                        f"Section {section_name}: {section_bars} bars not multiple of "
                        f"cycle {cycle} (prog len {len(prog)} × {bpc} bpc)"
                    ),
                )
            )
    return out


def check_hard_rules(
    skeleton: dict[str, Any], rendered: dict[str, Any] | None = None
) -> list[Violation]:
    """Run all hard-rule checks; optional rendered dict for LH rules."""
    violations: list[Violation] = []
    violations.extend(_check_chord_spelling(skeleton))
    violations.extend(_check_section_no_cadence(skeleton))
    violations.extend(_check_phrase_no_cadence(skeleton))
    violations.extend(_check_leap_not_recovered(skeleton))
    violations.extend(_check_melody_no_long_note(skeleton))
    violations.extend(_check_melody_no_rest(skeleton))
    violations.extend(_check_range_exceeded(skeleton, rendered))
    violations.extend(_check_density_mismatch(skeleton))
    violations.extend(_check_harmonic_rhythm_orphan(skeleton))
    if rendered is not None:
        violations.extend(_check_lh_parallel_fifths(skeleton, rendered))
    return violations


def format_violations(violations: list[Violation]) -> str:
    lines = []
    for v in violations:
        bar = f"bar {v.bar}" if v.bar is not None else "piece"
        lines.append(f"[{v.severity}] {v.rule_id} @ {bar}: {v.detail}")
    return "\n".join(lines)
