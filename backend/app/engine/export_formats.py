from __future__ import annotations

import base64
import tempfile
from pathlib import Path

from music21 import key, meter, note, stream, tempo

from app.engine.types import NoteEvent, PieceDraft

_PART_NAMES = {
    "piano_lh": "Piano LH",
    "piano_rh": "Piano RH",
    "bandoneon": "Bandoneón",
    "violin": "Violin",
    "cello": "Cello",
    "strings": "Strings",
}


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

    for n in draft.notes:
        m21 = note.Note(n.pitch)
        m21.volume.velocity = n.velocity
        offset = to_ql(n.start)
        m21.quarterLength = to_ql(n.duration)
        target = parts.get(n.track) or parts["piano_rh"]
        target.insert(offset, m21)

    # Insert parts that have content (RH before LH for piano-score reading habit)
    for track_id in ("piano_rh", "piano_lh", "bandoneon", "violin", "cello", "strings"):
        if track_id in parts and len(parts[track_id].notes) > 0:
            score.insert(0, parts[track_id])
    return score


def score_to_musicxml(score: stream.Score) -> str:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "piece.musicxml"
        score.write("musicxml", fp=str(path))
        return path.read_text(encoding="utf-8")


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
