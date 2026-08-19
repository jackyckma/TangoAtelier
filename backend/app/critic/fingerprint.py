"""Statistical fingerprint extraction and KL comparison."""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

REF_PATH = Path(__file__).resolve().parent / "reference" / "golden_age.json"

INTERVAL_BUCKETS = list(range(-12, 13))


@dataclass
class Fingerprint:
    interval_hist: dict[int, float] = field(default_factory=dict)
    onset_hist: dict[float, float] = field(default_factory=dict)
    duration_hist: dict[str, float] = field(default_factory=dict)
    chord_transition: dict[str, dict[str, float]] = field(default_factory=dict)
    notes_per_bar: float = 0.0
    rest_ratio: float = 0.0
    repeated_note_ratio: float = 0.0
    leap_ratio: float = 0.0


def _lead_notes(skeleton: dict[str, Any]) -> list[dict[str, Any]]:
    notes = skeleton.get("melody") or []
    lead = [n for n in notes if n.get("voice", "lead") == "lead"]
    return lead if lead else list(notes)


def _duration_category(duration_beats: float) -> str:
    if duration_beats < 0.375:
        return "sixteenth"
    if duration_beats < 0.625:
        return "eighth"
    if duration_beats < 1.25:
        return "quarter"
    if duration_beats < 2.5:
        return "half"
    return "long"


def _normalize_hist(hist: dict[Any, float]) -> dict[Any, float]:
    total = sum(hist.values())
    if total <= 0:
        return {k: 0.0 for k in hist}
    return {k: v / total for k, v in hist.items()}


def _kl_divergence(p: dict[Any, float], q: dict[Any, float], *, epsilon: float = 1e-10) -> float:
    keys = set(p) | set(q)
    if not keys:
        return 0.0
    p_n = _normalize_hist({k: p.get(k, 0.0) for k in keys})
    q_n = _normalize_hist({k: q.get(k, 0.0) for k in keys})
    kl = 0.0
    for k in keys:
        pk = max(p_n.get(k, 0.0), epsilon)
        qk = max(q_n.get(k, 0.0), epsilon)
        kl += pk * math.log(pk / qk)
    return kl


def extract_fingerprint(skeleton: dict[str, Any]) -> Fingerprint:
    """Extract comparable statistical distributions from a skeleton."""
    bpb = float(skeleton.get("beats_per_bar") or 2)
    total_bars = int(skeleton.get("bars") or 0)
    notes = sorted(_lead_notes(skeleton), key=lambda n: float(n["start_beat"]))

    interval_hist: dict[int, float] = {b: 0.0 for b in INTERVAL_BUCKETS}
    intervals_raw: list[int] = []
    for a, b in zip(notes, notes[1:]):
        iv = int(b["pitch"]) - int(a["pitch"])
        iv = max(-12, min(12, iv))
        interval_hist[iv] = interval_hist.get(iv, 0.0) + 1.0
        intervals_raw.append(iv)

    onset_hist: dict[float, float] = {}
    duration_hist: dict[str, float] = {}
    notes_per_bar_counts: dict[int, int] = {}
    for n in notes:
        beat_in_bar = round(float(n["start_beat"]) % bpb, 4)
        onset_hist[beat_in_bar] = onset_hist.get(beat_in_bar, 0.0) + 1.0
        cat = _duration_category(float(n["duration_beats"]))
        duration_hist[cat] = duration_hist.get(cat, 0.0) + 1.0
        bar = int(float(n["start_beat"]) // bpb)
        notes_per_bar_counts[bar] = notes_per_bar_counts.get(bar, 0) + 1

    bars_with_notes = set(notes_per_bar_counts)
    rest_ratio = 0.0
    if total_bars > 0:
        rest_ratio = (total_bars - len(bars_with_notes)) / total_bars

    n_intervals = len(intervals_raw)
    repeated = sum(1 for iv in intervals_raw if iv == 0)
    leaps = sum(1 for iv in intervals_raw if abs(iv) >= 5)
    repeated_note_ratio = repeated / n_intervals if n_intervals else 0.0
    leap_ratio = leaps / n_intervals if n_intervals else 0.0

    notes_per_bar = 0.0
    if total_bars > 0:
        notes_per_bar = len(notes) / total_bars

    chord_symbols = [str(c["symbol"]) for c in skeleton.get("chords") or []]
    chord_transition: dict[str, dict[str, float]] = {}
    for a, b in zip(chord_symbols, chord_symbols[1:]):
        row = chord_transition.setdefault(a, {})
        row[b] = row.get(b, 0.0) + 1.0

    return Fingerprint(
        interval_hist=_normalize_hist(interval_hist),
        onset_hist=_normalize_hist(onset_hist),
        duration_hist=_normalize_hist(duration_hist),
        chord_transition=chord_transition,
        notes_per_bar=notes_per_bar,
        rest_ratio=rest_ratio,
        repeated_note_ratio=repeated_note_ratio,
        leap_ratio=leap_ratio,
    )


def _fp_from_ref_block(block: dict[str, Any]) -> Fingerprint:
    interval = {int(k): float(v) for k, v in block.get("interval_hist", {}).items()}
    onset = {float(k): float(v) for k, v in block.get("onset_hist", {}).items()}
    duration = {str(k): float(v) for k, v in block.get("duration_hist", {}).items()}
    return Fingerprint(
        interval_hist=interval,
        onset_hist=onset,
        duration_hist=duration,
        notes_per_bar=float(block.get("notes_per_bar", 0)),
        rest_ratio=float(block.get("rest_ratio", 0)),
        repeated_note_ratio=float(block.get("repeated_note_ratio", 0)),
        leap_ratio=float(block.get("leap_ratio", 0)),
    )


def load_reference(dance_type: str, path: Path | None = None) -> Fingerprint:
    data = json.loads((path or REF_PATH).read_text(encoding="utf-8"))
    if dance_type not in data:
        raise KeyError(f"No reference fingerprint for dance_type={dance_type!r}")
    return _fp_from_ref_block(data[dance_type])


def compare(fp: Fingerprint, ref: Fingerprint) -> dict[str, float]:
    """Return KL divergence per dimension (and scalar deltas for ratios)."""
    ref_interval = {int(k): float(v) for k, v in ref.interval_hist.items()}
    ref_onset = {float(k): float(v) for k, v in ref.onset_hist.items()}
    ref_duration = {str(k): float(v) for k, v in ref.duration_hist.items()}

    return {
        "interval_hist": _kl_divergence(fp.interval_hist, ref_interval),
        "onset_hist": _kl_divergence(fp.onset_hist, ref_onset),
        "duration_hist": _kl_divergence(fp.duration_hist, ref_duration),
        "notes_per_bar_delta": abs(fp.notes_per_bar - ref.notes_per_bar),
        "rest_ratio_delta": abs(fp.rest_ratio - ref.rest_ratio),
        "repeated_note_ratio_delta": abs(fp.repeated_note_ratio - ref.repeated_note_ratio),
        "leap_ratio_delta": abs(fp.leap_ratio - ref.leap_ratio),
    }


def aggregate(fps: list[Fingerprint]) -> Fingerprint:
    """Average histograms and scalars across many fingerprints."""
    if not fps:
        return Fingerprint()

    def _avg_hist(key: str, cast_key):
        acc: dict[Any, float] = {}
        for fp in fps:
            hist = getattr(fp, key)
            for k, v in hist.items():
                ck = cast_key(k)
                acc[ck] = acc.get(ck, 0.0) + float(v)
        n = len(fps)
        return {k: v / n for k, v in acc.items()}

    return Fingerprint(
        interval_hist=_avg_hist("interval_hist", int),
        onset_hist=_avg_hist("onset_hist", float),
        duration_hist=_avg_hist("duration_hist", str),
        chord_transition={},
        notes_per_bar=sum(fp.notes_per_bar for fp in fps) / len(fps),
        rest_ratio=sum(fp.rest_ratio for fp in fps) / len(fps),
        repeated_note_ratio=sum(fp.repeated_note_ratio for fp in fps) / len(fps),
        leap_ratio=sum(fp.leap_ratio for fp in fps) / len(fps),
    )
