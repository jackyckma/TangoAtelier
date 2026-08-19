# BASELINE 2026-08-19: tango error violations present on all 50 seeds (DENSITY_MISMATCH, etc.)
# Fingerprint KL baselines recorded in test_fingerprint.py

from __future__ import annotations

import pytest

from app.critic.rules import check_hard_rules, format_violations
from app.engine import SIMPLE_PROFILE, render_skeleton
from app.engine.skeleton import build_skeleton


@pytest.mark.parametrize("dance", ["tango", "vals", "milonga"])
@pytest.mark.parametrize("seed", range(1, 51))
def test_no_error_violations(dance: str, seed: int) -> None:
    sk = build_skeleton(dance_type=dance, seed=seed)
    rendered = render_skeleton(
        sk, SIMPLE_PROFILE, seed=sk["seed"], include_midi=False, include_musicxml=False
    )
    errors = [v for v in check_hard_rules(sk, rendered) if v.severity == "error"]
    assert not errors, format_violations(errors)


def test_descending_fifths_spells_bvii_correctly() -> None:
    """§1 bug 1 fixed: bVII in A minor = G–B–D pitch classes."""
    from app.engine.harmony import chord_pitches

    for seed in range(1, 201):
        sk = build_skeleton(
            dance_type="tango",
            seed=seed,
            progression_id="descending_fifths",
        )
        if sk.get("progression_id") != "descending_fifths":
            continue
        assert "bVII" in sk.get("progression") or "bVII" in str(sk.get("chords"))
        pcs = frozenset(p % 12 for p in chord_pitches(57, "minor", "bVII"))
        assert pcs == frozenset({7, 11, 2}), f"bVII PCs {pcs}"
        rendered = render_skeleton(
            sk, SIMPLE_PROFILE, seed=sk["seed"], include_midi=False, include_musicxml=False
        )
        spelling = [
            v for v in check_hard_rules(sk, rendered) if v.rule_id == "CHORD_SPELLING_INVALID"
        ]
        assert not spelling, format_violations(spelling)
        break
    else:
        raise AssertionError("No descending_fifths skeleton in 200 seeds")


def test_no_chord_spelling_violations_tango_sample() -> None:
    """M1 DoD: CHORD_SPELLING_INVALID should be zero on a tango seed batch."""
    from collections import Counter

    counts: Counter[str] = Counter()
    for seed in range(1, 101):
        sk = build_skeleton(dance_type="tango", seed=seed)
        rendered = render_skeleton(
            sk, SIMPLE_PROFILE, seed=sk["seed"], include_midi=False, include_musicxml=False
        )
        for v in check_hard_rules(sk, rendered):
            if v.rule_id == "CHORD_SPELLING_INVALID":
                counts[v.rule_id] += 1
    assert counts["CHORD_SPELLING_INVALID"] == 0


def test_musicxml_includes_harmony() -> None:
    sk = build_skeleton(dance_type="tango", seed=7, progression_id="descending_fifths")
    out = render_skeleton(
        sk, SIMPLE_PROFILE, seed=sk["seed"], include_midi=False, include_musicxml=True
    )
    xml = out.get("musicxml") or ""
    assert "<harmony" in xml
    assert len(xml) > 500


def test_iio7_has_seventh() -> None:
    """§1 bug 2 fixed: iiø7 includes the 7th (A in A minor)."""
    from app.engine.harmony import chord_pitches

    pcs = frozenset(p % 12 for p in chord_pitches(57, "minor", "iiø7"))
    assert pcs == frozenset({11, 2, 5, 9}), f"iiø7 PCs {pcs}"


def test_m2_phrase_harmony_cadence_rules_zero() -> None:
    """M2 DoD: section/phrase cadence + harmonic rhythm orphan on golden_age forms."""
    from collections import Counter

    rules = ("SECTION_NO_CADENCE", "PHRASE_NO_CADENCE", "HARMONIC_RHYTHM_ORPHAN")
    counts: Counter[str] = Counter()
    for dance in ("tango", "vals", "milonga"):
        n = 100 if dance == "tango" else 50
        for seed in range(1, n + 1):
            sk = build_skeleton(dance_type=dance, seed=seed, form_id="golden_age_short")
            rendered = render_skeleton(
                sk, SIMPLE_PROFILE, seed=sk["seed"], include_midi=False, include_musicxml=False
            )
            for v in check_hard_rules(sk, rendered):
                if v.rule_id in rules:
                    counts[v.rule_id] += 1
    assert counts["SECTION_NO_CADENCE"] == 0
    assert counts["PHRASE_NO_CADENCE"] == 0
    assert counts["HARMONIC_RHYTHM_ORPHAN"] == 0


def test_b_section_relative_modulation_when_progression_locked() -> None:
    """B moves to relative major/minor even when the user picked a progression."""
    sk = build_skeleton(
        dance_type="tango",
        seed=1,
        progression_id="descending_fifths",
        form_id="golden_age_short",
    )
    home = (sk["key"], sk["mode"], sk["tonic"])
    b = next(s for s in sk["harmony_plan"] if s["section"] == "B")
    assert (b["key"], b["mode"], b["tonic"]) != home
    assert str(b.get("modulation") or "").startswith("relative")


def test_golden_age_short_has_v7_bridge_before_b() -> None:
    """A → 4-bar V7 pedal bridge → relative B."""
    sk = build_skeleton(dance_type="tango", seed=1, form_id="golden_age_short")
    names = [s["section"] for s in sk["harmony_plan"]]
    assert names == ["intro", "A", "bridge", "B", "A_prime", "coda"]
    assert sk["bars"] == 60
    bridge = next(s for s in sk["harmony_plan"] if s["section"] == "bridge")
    assert bridge["bar_to"] - (bridge["bar_from"] - 1) == 4
    bridge_chords = [
        c for c in sk["chords"] if bridge["bar_from"] - 1 <= c["bar"] < bridge["bar_to"]
    ]
    assert all(c["symbol"] == "V7" for c in bridge_chords)
    b = next(s for s in sk["harmony_plan"] if s["section"] == "B")
    assert b["bar_from"] == bridge["bar_to"] + 1


def test_m2_harmonic_rhythm_orphan_skips_per_bar_template() -> None:
    """Per-bar progression_template (len == section bars) must not trigger orphan."""
    sk = build_skeleton(dance_type="tango", seed=7, form_id="golden_age_short")
    rendered = render_skeleton(
        sk, SIMPLE_PROFILE, seed=sk["seed"], include_midi=False, include_musicxml=False
    )
    orphans = [
        v for v in check_hard_rules(sk, rendered) if v.rule_id == "HARMONIC_RHYTHM_ORPHAN"
    ]
    assert not orphans, format_violations(orphans)


def test_critic_detects_harmonic_rhythm_orphan_legacy_cycle() -> None:
    """Legacy 2-bar/chord grid with section length not multiple of cycle."""
    sk = build_skeleton(dance_type="tango", seed=7, form_id="abab")
    for sec in sk["harmony_plan"]:
        if sec.get("section") == "A":
            sec["progression_template"] = []
            sec["bars_per_chord"] = 2
            # 15 bars vs 4-chord × 2 bpc = 8-bar cycle → orphan
            sec["bar_to"] = int(sec["bar_from"]) + 14
            break
    rendered = render_skeleton(
        sk, SIMPLE_PROFILE, seed=sk["seed"], include_midi=False, include_musicxml=False
    )
    orphans = [
        v for v in check_hard_rules(sk, rendered) if v.rule_id == "HARMONIC_RHYTHM_ORPHAN"
    ]
    assert orphans, "15-bar section vs 8-bar cycle should trigger HARMONIC_RHYTHM_ORPHAN"
