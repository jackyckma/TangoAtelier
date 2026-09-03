"""Abstract chord/phrase features from MusicXML — no pitch-level output."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from music21 import converter, harmony, stream

_ALLOWED_KEYS = frozenset({"chord_symbols", "bars", "phrase_bar_lengths", "source_path"})


def extract_abstract(musicxml_path: str | Path) -> dict[str, Any]:
    """Read one MusicXML file and return abstract harmonic/phrase metadata only."""
    path = Path(musicxml_path)
    score = converter.parse(str(path))
    measures = _collect_measures(score)
    bars = len(measures)
    chord_symbols = _extract_chord_symbols(measures)
    phrase_bar_lengths = _heuristic_phrase_lengths(chord_symbols, bars)

    result = {
        "chord_symbols": chord_symbols,
        "bars": bars,
        "phrase_bar_lengths": phrase_bar_lengths,
        "source_path": path.name,
    }
    if set(result) - _ALLOWED_KEYS:
        raise ValueError("extract_abstract produced disallowed keys")
    return result


def _collect_measures(score: stream.Score) -> list[stream.Measure]:
    parts = score.parts
    if parts:
        return list(parts[0].getElementsByClass(stream.Measure))
    return list(score.recurse().getElementsByClass(stream.Measure))


def _extract_chord_symbols(measures: list[stream.Measure]) -> list[str]:
    symbols: list[str] = []
    for measure in measures:
        chords = list(measure.getElementsByClass(harmony.ChordSymbol))
        if chords:
            figure = chords[0].figure
            symbols.append(figure if figure else chords[0].symbol)
        else:
            symbols.append("")
    return symbols


def _heuristic_phrase_lengths(chord_symbols: list[str], bars: int) -> list[int]:
    """Split at cadence points; fall back to 4-bar phrases."""
    if bars <= 0:
        return []

    split_points: set[int] = set()

    for i in range(1, len(chord_symbols)):
        prev_root = _root_letter(chord_symbols[i - 1])
        curr_root = _root_letter(chord_symbols[i])
        if prev_root and curr_root and _fifth_above(curr_root) == prev_root:
            split_points.add(i)

    tonic = _root_letter(chord_symbols[0]) if chord_symbols else None
    if tonic:
        dominant = _fifth_above(tonic)
        for i, sym in enumerate(chord_symbols[:-1]):
            if _root_letter(sym) == dominant:
                split_points.add(i + 1)

    if not split_points:
        return _chunk_by_size(bars, 4)

    phrase_lengths: list[int] = []
    start = 0
    for end in sorted(split_points):
        if end <= start:
            continue
        phrase_lengths.append(end - start)
        start = end
    tail = bars - start
    if tail > 0:
        phrase_lengths.append(tail)
    return phrase_lengths or [bars]


def _chunk_by_size(total: int, size: int) -> list[int]:
    chunks: list[int] = []
    remaining = total
    while remaining > 0:
        take = min(size, remaining)
        chunks.append(take)
        remaining -= take
    return chunks


def _root_letter(symbol: str) -> str | None:
    if not symbol:
        return None
    letter = symbol[0].upper()
    return letter if letter in "ABCDEFG" else None


def _fifth_above(root: str) -> str:
    order = "FCGDAEB"
    idx = order.index(root)
    return order[(idx + 1) % len(order)]
