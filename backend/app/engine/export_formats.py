from __future__ import annotations

import base64
import tempfile
from pathlib import Path

from music21 import harmony, key, meter, note, pitch, stream, tempo

from app.engine.harmony_vocab import chord_spec
from app.engine.types import NoteEvent, PieceDraft

_PART_NAMES = {
    "piano_lh": "Piano LH",
    "piano_rh": "Piano RH",
    "bandoneon": "Bandoneón",
    "violin": "Violin",
    "cello": "Cello",
    "strings": "Strings",
}


def _chord_root_name(p: pitch.Pitch) -> str:
    n = p.name
    if n.endswith("-"):
        return f"{n[:-1]}b"
    return n


def _lead_sheet_figure(symbol: str, mode: str, tonic_midi: int) -> str:
    spec = chord_spec(symbol, mode)
    root = pitch.Pitch(tonic_midi + spec.root_semitones)
    base = _chord_root_name(root)
    iv = spec.intervals
    if iv == (0, 3, 7):
        return f"{base}m"
    if iv == (0, 4, 7):
        return base
    if iv == (0, 4, 7, 10):
        return f"{base}7"
    if iv == (0, 3, 6, 10):
        return f"{base}m7b5"
    if iv == (0, 3, 6):
        return f"{base}dim"
    if iv == (0, 4, 7, 10, 13):
        return f"{base}7b9"
    if iv == (0, 3, 7, 9):
        return f"{base}m6"
    if iv == (0, 3, 7, 10):
        return f"{base}m7"
    if iv == (0, 3, 7, 11):
        return f"{base}m(maj7)"
    if iv == (0, 4, 8):
        return f"{base}+"
    return spec.symbol


def _chord_harmony(ch, draft: PieceDraft):
    mode = ch.mode or draft.mode
    try:
        fig = _lead_sheet_figure(ch.symbol, mode, ch.tonic)
        cs = harmony.ChordSymbol(fig)
        cs.quarterLength = 0.0
        return cs
    except Exception:
        return None


def _quantize_ql(ql: float, grid: float = 0.25) -> float:
    if ql <= 0:
        return grid
    return max(grid, round(ql / grid) * grid)


def draft_to_score(draft: PieceDraft) -> stream.Score:
    score = stream.Score()
    score.insert(0, tempo.MetronomeMark(number=draft.bpm))
    score.insert(0, meter.TimeSignature(f"{draft.time_signature[0]}/{draft.time_signature[1]}"))

    key_parts = draft.key_name.split()
    tonic_name = key_parts[0]
    mode = key_parts[1] if len(key_parts) > 1 else "minor"
    score.insert(0, key.Key(tonic_name, mode))

    parts: dict[str, stream.Part] = {}
    for track_id, name in _PART_NAMES.items():
        p = stream.Part(id=track_id)
        p.partName = name
        parts[track_id] = p

    def to_ql(seconds: float) -> float:
        return max(0.05, seconds * draft.bpm / 60.0)

    harmony_part = stream.Part(id="chords")
    harmony_part.partName = "Chords"
    seen_harmony: set[tuple[int, str]] = set()
    for ch in draft.chords:
        dedupe = (int(round(to_ql(ch.start) * 100)), ch.symbol)
        if dedupe in seen_harmony:
            continue
        seen_harmony.add(dedupe)
        h = _chord_harmony(ch, draft)
        if h is not None:
            harmony_part.insert(_quantize_ql(to_ql(ch.start)), h)

    for n in draft.notes:
        m21 = note.Note(n.pitch)
        m21.volume.velocity = n.velocity
        offset = _quantize_ql(to_ql(n.start))
        m21.quarterLength = _quantize_ql(to_ql(n.duration))
        target = parts.get(n.track) or parts["piano_rh"]
        target.insert(offset, m21)

    if len(harmony_part.getElementsByClass(harmony.Harmony)) > 0:
        score.insert(0, harmony_part)

    for track_id in ("piano_rh", "piano_lh", "bandoneon", "violin", "cello", "strings"):
        if track_id in parts and len(parts[track_id].notes) > 0:
            score.insert(0, parts[track_id])
    return score


def score_to_musicxml(score: stream.Score) -> str:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "piece.musicxml"
        score.write("musicxml", fp=str(path))
        xml = path.read_text(encoding="utf-8")
        return xml


def score_to_midi_base64(score: stream.Score) -> str:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "piece.mid"
        score.write("midi", fp=str(path))
        return base64.b64encode(path.read_bytes()).decode("ascii")


def notes_payload(notes: list[NoteEvent]) -> list[dict]:
    return [
        {
            "pitch": n.pitch,
            "start": round(n.start, 4),
            "duration": round(n.duration, 4),
            "velocity": n.velocity,
            "track": n.track,
        }
        for n in notes
    ]
