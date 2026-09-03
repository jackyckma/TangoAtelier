"""Tests for abstract MusicXML knowledge extraction."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.knowledge.extract_abstract import extract_abstract

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "knowledge" / "minimal_phrase.musicxml"


def test_fixture_exists():
    assert FIXTURE.is_file()


def test_extract_returns_allowed_keys_only():
    result = extract_abstract(FIXTURE)
    assert set(result) == {"chord_symbols", "bars", "phrase_bar_lengths", "source_path"}


def test_extract_chord_symbols_and_bars():
    result = extract_abstract(FIXTURE)
    assert result["source_path"] == "minimal_phrase.musicxml"
    assert result["bars"] == 4
    assert isinstance(result["chord_symbols"], list)
    assert len(result["chord_symbols"]) == 4
    assert "C" in result["chord_symbols"][0]
    assert "G" in result["chord_symbols"][1]


def test_extract_no_pitch_fields():
    result = extract_abstract(FIXTURE)
    assert "pitches" not in result
    assert "melody" not in result
    assert "notes" not in result


def test_phrase_bar_lengths_sum_to_bars():
    result = extract_abstract(FIXTURE)
    lengths = result["phrase_bar_lengths"]
    assert isinstance(lengths, list)
    assert all(isinstance(n, int) and n > 0 for n in lengths)
    assert sum(lengths) == result["bars"]


def test_missing_file_raises():
    with pytest.raises(Exception):
        extract_abstract("nonexistent_fixture.musicxml")
