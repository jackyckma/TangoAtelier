"""M10 — Pulse / groove rendering checks."""

from __future__ import annotations

import statistics
from collections import Counter

from app.critic.rules import check_hard_rules
from app.data_loader import load_orchestra
from app.engine import SIMPLE_PROFILE, render_skeleton
from app.engine.groove import pattern_for_groove_bar, resolve_pulse
from app.engine.skeleton import build_skeleton


def _render(profile_id: str, seed: int = 7, dance: str = "tango") -> tuple[dict, dict]:
    sk = build_skeleton(dance_type=dance, seed=seed, form_id="golden_age_short")
    profile = SIMPLE_PROFILE if profile_id == "simple" else load_orchestra(profile_id)
    out = render_skeleton(
        sk, profile, seed=sk["seed"], include_midi=False, include_musicxml=False
    )
    return sk, out


def _lh_notes(rendered: dict) -> list[dict]:
    return [
        n
        for n in rendered["notes"]
        if n.get("track") in ("piano_lh", "piano_lh_chord")
    ]


def test_di_sarli_chord_layer_lags_bass() -> None:
    _, out = _render("di_sarli", seed=11)
    bpm = float(out["bpm"])
    bar_len = 2 * (60.0 / bpm)
    bass_onsets = [float(n["start"]) for n in _lh_notes(out) if n["track"] == "piano_lh"]
    chord_onsets = [float(n["start"]) for n in _lh_notes(out) if n["track"] == "piano_lh_chord"]
    assert chord_onsets, "expected piano_lh_chord hits for Di Sarli blocks"
    lags_ms: list[float] = []
    for c in chord_onsets:
        candidates = [b for b in bass_onsets if abs(b - c) < bar_len]
        if not candidates:
            continue
        earlier = [b for b in candidates if b <= c + 0.002]
        b = max(earlier) if earlier else min(candidates, key=lambda x: abs(x - c))
        lags_ms.append((c - b) * 1000.0)
    assert lags_ms
    mean_lag = statistics.mean(lags_ms)
    assert mean_lag >= 15.0, f"mean chord lag {mean_lag:.1f}ms < 15ms"


def test_pugliese_chord_layer_lags_bass() -> None:
    _, out = _render("pugliese", seed=13)
    chord = [n for n in _lh_notes(out) if n["track"] == "piano_lh_chord"]
    bass = [n for n in _lh_notes(out) if n["track"] == "piano_lh"]
    assert chord and bass
    exp = float(out["pulse"]["chord_lag_ms"]) / 1000.0
    lags: list[float] = []
    for c in chord:
        # Pair chord hit with bass that shares the pre-lag onset (±30ms + humanize)
        targets = [
            b
            for b in bass
            if abs((float(c["start"]) - exp) - float(b["start"])) < 0.035
        ]
        if not targets:
            continue
        b0 = min(targets, key=lambda b: abs((float(c["start"]) - exp) - float(b["start"])))
        lags.append((float(c["start"]) - float(b0["start"])) * 1000.0)
    assert lags
    assert statistics.mean(lags) >= 15.0


def _beat1_ratio(sk: dict, out: dict) -> float:
    bpm = float(out["bpm"])
    spb = 60.0 / bpm
    bar_len = 2 * spb
    meta = {int(c["bar"]): c for c in sk["chords"]}
    beat1: list[int] = []
    other: list[int] = []
    for n in out["notes"]:
        if n.get("track") != "piano_lh":
            continue
        bar = int(float(n["start"]) / bar_len)
        ch = meta.get(bar) or {}
        if ch.get("section") not in ("A", "B", "A_prime"):
            continue
        if ch.get("drama") in ("pause", "anticipate"):
            continue
        local = float(n["start"]) % bar_len
        if local < spb * 0.4:
            beat1.append(int(n["velocity"]))
        elif local >= spb * 0.55:
            other.append(int(n["velocity"]))
    if not beat1 or not other:
        return 0.0
    return statistics.median(beat1) / max(1, statistics.median(other))


def test_orquesta_beat1_velocity_ratio_band() -> None:
    """Aggregate bass beat-1 / other-beat velocity ratio over several seeds."""
    for oid in ("di_sarli", "d_arienzo", "troilo", "canaro"):
        ratios = []
        for seed in range(1, 9):
            sk, out = _render(oid, seed=seed)
            r = _beat1_ratio(sk, out)
            if r > 0:
                ratios.append(r)
        assert ratios, f"{oid}: no measurable ratios"
        agg = statistics.median(ratios)
        assert 1.12 <= agg <= 1.40, f"{oid} beat1_velocity_ratio median={agg:.3f} raw={ratios}"


def test_b_section_has_continuous_non_marcato_run() -> None:
    sk, out = _render("d_arienzo", seed=5)
    patterns = out.get("lh_pattern_by_bar") or {}
    b_bars = sorted(int(c["bar"]) for c in sk["chords"] if c.get("section") == "B")
    assert len(b_bars) >= 8
    seq = [patterns.get(str(b), "") for b in b_bars]
    best = cur = 0
    for p in seq:
        if p and not str(p).startswith("marcato") and p not in ("pesante", "lyrical_phrasing"):
            cur += 1
            best = max(best, cur)
        else:
            cur = 0
    assert best >= 4, f"B pattern run={best} seq={seq}"


def test_a_sections_stay_marcato_home() -> None:
    sk, out = _render("simple", seed=5)
    patterns = out.get("lh_pattern_by_bar") or {}
    for section in ("A", "A_prime"):
        bars = [int(c["bar"]) for c in sk["chords"] if c.get("section") == section]
        homeish = 0
        for b in bars:
            p = patterns.get(str(b), "")
            if p.startswith("marcato") or p in ("pesante", "lyrical_phrasing", "milonga_habanera"):
                homeish += 1
        assert homeish / max(1, len(bars)) >= 0.85, f"{section} home ratio low"


def test_seed_reproducible_pulse_render() -> None:
    sk = build_skeleton(dance_type="tango", seed=42, form_id="golden_age_short")
    profile = load_orchestra("di_sarli")
    a = render_skeleton(sk, profile, seed=42, include_midi=False, include_musicxml=False)
    b = render_skeleton(sk, profile, seed=42, include_midi=False, include_musicxml=False)
    assert a["notes"] == b["notes"]
    assert a["lh_pattern_by_bar"] == b["lh_pattern_by_bar"]
    assert a["pulse"] == b["pulse"]


def test_groove_roles_on_skeleton() -> None:
    sk = build_skeleton(dance_type="tango", seed=3, form_id="golden_age_short")
    sg = sk["section_groove"]
    assert sg["intro"]["groove_role"] == "home"
    assert sg["A"]["groove_role"] == "home"
    assert sg["bridge"]["groove_role"] == "pivot"
    assert sg["B"]["groove_role"] == "contrast_drive"
    assert sg["B"]["contrast_run_bars"] in (4, 8)
    assert sg["A_prime"]["groove_role"] == "home_elevated"
    assert sg["coda"]["groove_role"] == "home_cadence"
    b0 = next(c for c in sk["chords"] if c["section"] == "B")
    assert "section_local_bar" in b0["groove"]
    assert "chord_lag_ms" not in b0["groove"]


def test_contrast_drive_pattern_helper_run_length() -> None:
    primary = "marcato_en_cuatro"
    secondary = "milonga_332"
    run_patterns = []
    for local in range(16):
        groove = {
            "groove_role": "contrast_drive",
            "contrast_run_bars": 8,
            "section_local_bar": local,
            "section_bars": 16,
        }
        run_patterns.append(
            pattern_for_groove_bar(primary, secondary, local, groove=groove, dance_type="tango")
        )
    best = cur = 0
    for p in run_patterns:
        if p == secondary:
            cur += 1
            best = max(best, cur)
        else:
            cur = 0
    assert best >= 4
    assert run_patterns[0] == primary
    assert run_patterns[-1] == primary


def test_m1_m2_still_zero_with_pulse_render() -> None:
    rules = (
        "CHORD_SPELLING_INVALID",
        "SECTION_NO_CADENCE",
        "PHRASE_NO_CADENCE",
        "HARMONIC_RHYTHM_ORPHAN",
    )
    counts: Counter[str] = Counter()
    for seed in range(1, 31):
        sk = build_skeleton(dance_type="tango", seed=seed, form_id="golden_age_short")
        out = render_skeleton(
            sk, SIMPLE_PROFILE, seed=sk["seed"], include_midi=False, include_musicxml=False
        )
        for v in check_hard_rules(sk, out):
            if v.rule_id in rules:
                counts[v.rule_id] += 1
    for r in rules:
        assert counts[r] == 0, f"{r}={counts[r]}"


def test_resolve_pulse_defaults_for_missing_block() -> None:
    p = resolve_pulse({"id": "unknown_orquesta"})
    assert p.feel == "drive"
    assert p.humanize_ms >= 15
    di = resolve_pulse(load_orchestra("di_sarli"))
    assert di.feel == "heart"
    assert di.chord_lag_ms >= 18
