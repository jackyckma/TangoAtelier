from __future__ import annotations

import base64
import tempfile
from pathlib import Path

from music21 import key, meter, note, stream, tempo

from app.engine.types import NoteEvent, PieceDraft


def draft_to_score(draft: PieceDraft) -> stream.Score:
    score = stream.Score()
    score.insert(0, tempo.MetronomeMark(number=draft.bpm))
    score.insert(0, meter.TimeSignature(f"{draft.time_signature[0]}/{draft.time_signature[1]}"))

    key_parts = draft.key_name.split()
    tonic_name = key_parts[0]
    mode = key_parts[1] if len(key_parts) > 1 else "minor"
    score.insert(0, key.Key(tonic_name, mode))

    part_lh = stream.Part(id="piano_lh")
    part_rh = stream.Part(id="piano_rh")
    part_lh.partName = "Piano LH"
    part_rh.partName = "Piano RH"

    # music21 uses quarterLength; convert seconds → QL via bpm
    # 1 quarter = 60/bpm seconds → ql = seconds * bpm / 60
    def to_ql(seconds: float) -> float:
        return max(0.05, seconds * draft.bpm / 60.0)

    # Group notes by approximate offset
    for n in draft.notes:
        m21 = note.Note(n.pitch)
        m21.volume.velocity = n.velocity
        offset = to_ql(n.start)
        m21.quarterLength = to_ql(n.duration)
        target = part_lh if n.track == "piano_lh" else part_rh
        target.insert(offset, m21)

    score.insert(0, part_rh)
    score.insert(0, part_lh)
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
