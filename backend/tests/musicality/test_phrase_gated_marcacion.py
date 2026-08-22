"""Phrase-gated marcación — bass rests follow M2 phrase boundaries + drama."""

from __future__ import annotations

import statistics

from app.data_loader import load_orchestra
from app.engine import render_skeleton
from app.engine.groove import (
    PulseParams,
    apply_phrase_gated_marcacion,
    phrase_gate_strength,
)
from app.engine.skeleton import build_skeleton
from app.engine.types import NoteEvent


def _lh_onsets_for_bar(rendered: dict, bar: int) -> list[float]:
    bpm = float(rendered["bpm"])
    bar_len = 2 * (60.0 / bpm)
    bar_start = bar * bar_len
    out: list[float] = []
    for n in rendered["notes"]:
        if n.get("track") != "piano_lh":
            continue
        start = float(n["start"])
        if bar_start - 1e-6 <= start < bar_start + bar_len - 1e-6:
            out.append(round((start - bar_start) / bar_len, 3))
    return sorted(out)


def _phrase_end_bars(sk: dict) -> list[dict]:
    return [c for c in sk["chords"] if c.get("phrase_end") and c.get("section") in ("A", "B", "A_prime")]


def test_skeleton_chords_carry_phrase_metadata() -> None:
    sk = build_skeleton(dance_type="tango", seed=7, form_id="golden_age_short")
    tagged = [c for c in sk["chords"] if "phrase_local_bar" in c]
    assert len(tagged) >= 20
    ends = _phrase_end_bars(sk)
    assert ends
    for ch in ends:
        assert ch["phrase_local_bar"] == ch["phrase_bars"] - 1


def test_phrase_end_bar_has_fewer_lh_onsets_than_open_bar() -> None:
    sk = build_skeleton(dance_type="tango", seed=7, form_id="golden_age_short")
    out = render_skeleton(
        sk, load_orchestra("di_sarli"), seed=sk["seed"], include_midi=False, include_musicxml=False
    )
    pairs: list[tuple[int, int]] = []
    for ch in _phrase_end_bars(sk):
        bar = int(ch["bar"])
        if ch.get("drama") in ("climax", "rise", "dense"):
            continue
        if float(ch.get("energy") or 0) >= 0.65:
            continue
        open_bar = bar - int(ch["phrase_local_bar"])
        open_ch = next((c for c in sk["chords"] if c["bar"] == open_bar), None)
        if not open_ch or open_ch.get("drama") in ("climax", "rise", "dense"):
            continue
        end_n = len(_lh_onsets_for_bar(out, bar))
        open_n = len(_lh_onsets_for_bar(out, open_bar))
        if open_n >= 2 and end_n > 0:
            pairs.append((open_n, end_n))
    assert pairs, "expected comparable phrase open/end LH pairs"
    thinned = sum(1 for o, e in pairs if e < o)
    assert thinned / len(pairs) >= 0.45, f"phrase-end thinning ratio low: {pairs}"


def test_climax_phrase_end_keeps_denser_marcato() -> None:
    sk = build_skeleton(dance_type="tango", seed=3, form_id="golden_age_short")
    out = render_skeleton(
        sk, load_orchestra("d_arienzo"), seed=sk["seed"], include_midi=False, include_musicxml=False
    )
    calm_ends: list[int] = []
    drive_ends: list[int] = []
    for ch in _phrase_end_bars(sk):
        bar = int(ch["bar"])
        n = len(_lh_onsets_for_bar(out, bar))
        if ch.get("drama") in ("climax", "rise", "dense") or float(ch.get("energy") or 0) >= 0.72:
            drive_ends.append(n)
        elif ch.get("drama") in ("normal", "release", "pause"):
            calm_ends.append(n)
    assert calm_ends and drive_ends
    assert statistics.median(drive_ends) >= statistics.median(calm_ends)


def test_phrase_gate_strength_respects_drive() -> None:
    pulse = PulseParams(silence_bias=0.16)
    calm = phrase_gate_strength(
        phrase_end=True,
        phrase_local_bar=1,
        phrase_bars=2,
        phrase_role="answer",
        drama_tag="normal",
        energy=0.35,
        pulse=pulse,
    )
    drive = phrase_gate_strength(
        phrase_end=True,
        phrase_local_bar=1,
        phrase_bars=2,
        phrase_role="answer",
        drama_tag="climax",
        energy=0.85,
        pulse=pulse,
    )
    assert calm > drive
    assert drive < 0.15


def test_milonga_phrase_end_thins_habanera_tail() -> None:
    sk = build_skeleton(dance_type="milonga", seed=11, form_id="golden_age_short")
    out = render_skeleton(
        sk, load_orchestra("canaro"), seed=sk["seed"], include_midi=False, include_musicxml=False
    )
    pairs: list[tuple[int, int]] = []
    for ch in _phrase_end_bars(sk):
        bar = int(ch["bar"])
        pat = (out.get("lh_pattern_by_bar") or {}).get(str(bar), "")
        if pat not in ("milonga_habanera", "milonga_332"):
            continue
        if ch.get("drama") in ("climax", "rise", "dense"):
            continue
        open_bar = bar - int(ch["phrase_local_bar"])
        end_n = len(_lh_onsets_for_bar(out, bar))
        open_n = len(_lh_onsets_for_bar(out, open_bar))
        if open_n >= 2 and end_n > 0:
            pairs.append((open_n, end_n))
    assert pairs
    assert sum(1 for o, e in pairs if e < o) >= 1


def test_apply_phrase_gate_unit_4_plus_1() -> None:
    pulse = PulseParams(silence_bias=0.16)
    bar_len = 2.0
    notes = [
        NoteEvent(pitch=36, start=i * 0.5, duration=0.3, velocity=90, track="piano_lh")
        for i in range(4)
    ]
    gated = apply_phrase_gated_marcacion(
        notes,
        bar_start=0.0,
        bar_len=bar_len,
        beats_per_bar=2,
        pattern="marcato_en_cuatro",
        phrase_local_bar=1,
        phrase_bars=2,
        phrase_role="answer",
        phrase_end=True,
        drama_tag="normal",
        energy=0.4,
        pulse=pulse,
        section="A",
    )
    assert len(gated) == 1
    assert gated[0].start == 0.0
