from __future__ import annotations

import random

from app.engine.export_formats import (
    draft_to_score,
    notes_payload,
    score_to_midi_base64,
    score_to_musicxml,
)
from app.engine.harmony import build_chord_plan, chord_pitches, pick_key
from app.engine.melody import right_hand_for_bar
from app.engine.rhythm import (
    bar_duration_seconds,
    choose_rhythm_pattern,
    left_hand_for_bar,
)
from app.engine.types import ChordEvent, PieceDraft


FORM_BARS = {
    "intro": 4,
    "A": 20,
    "A_prime": 20,
    "coda": 4,
}


def _bpm_for(profile: dict, rng: random.Random) -> float:
    lo, hi = profile.get("tempo_bpm_range", [60, 66])
    return float(rng.randint(int(lo), int(hi)))


def generate_piece(
    profile: dict,
    seed: int | None = None,
    *,
    include_musicxml: bool = False,
    include_midi: bool = True,
) -> dict:
    seed = int(seed if seed is not None else random.randint(1, 2_147_483_647))
    rng = random.Random(seed)

    bpm = _bpm_for(profile, rng)
    key_name, mode, tonic = pick_key(rng, profile)
    time_signature = (2, 4)
    rhythm = choose_rhythm_pattern(profile)
    articulation = profile.get("articulation", {})

    form = ["intro", "A", "A_prime", "coda"]
    total_bars = sum(FORM_BARS[s] for s in form)
    bar_len = bar_duration_seconds(bpm, time_signature)

    chord_plan = build_chord_plan(rng, profile, mode, total_bars, bars_per_chord=2)
    # Map bar → symbol
    chord_at_bar: dict[int, str] = {}
    for start_bar, symbol in chord_plan:
        for b in range(start_bar, start_bar + 2):
            chord_at_bar[b] = symbol

    draft = PieceDraft(
        orchestra_id=profile["id"],
        seed=seed,
        bpm=bpm,
        key_name=key_name,
        mode=mode,
        time_signature=time_signature,
        rhythm_pattern=rhythm,
        form=form,
        bars=total_bars,
    )

    bar_index = 0
    for section in form:
        ornate = section == "A_prime"
        for _ in range(FORM_BARS[section]):
            symbol = chord_at_bar.get(bar_index, "i" if mode == "minor" else "I")
            pitches = chord_pitches(tonic, mode, symbol)
            bar_start = bar_index * bar_len

            draft.chords.append(
                ChordEvent(
                    bar=bar_index,
                    symbol=symbol,
                    start=bar_start,
                    duration=bar_len,
                )
            )
            draft.notes.extend(
                left_hand_for_bar(
                    rhythm, bar_index, bar_start, bar_len, pitches, articulation
                )
            )
            draft.notes.extend(
                right_hand_for_bar(
                    rng,
                    bar_index,
                    bar_start,
                    bar_len,
                    tonic,
                    mode,
                    pitches,
                    articulation,
                    ornate=ornate,
                )
            )
            bar_index += 1

    draft.notes.sort(key=lambda n: (n.start, n.track, n.pitch))
    score = draft_to_score(draft)

    duration = total_bars * bar_len
    payload = {
        "orchestra_id": draft.orchestra_id,
        "seed": draft.seed,
        "bpm": draft.bpm,
        "key": draft.key_name,
        "mode": draft.mode,
        "time_signature": list(draft.time_signature),
        "rhythm_pattern": draft.rhythm_pattern,
        "form": draft.form,
        "bars": draft.bars,
        "duration_seconds": round(duration, 2),
        "chords": [
            {
                "bar": c.bar,
                "symbol": c.symbol,
                "start": round(c.start, 4),
                "duration": round(c.duration, 4),
            }
            for c in draft.chords
        ],
        "notes": notes_payload(draft.notes),
    }
    if include_midi:
        payload["midi_base64"] = score_to_midi_base64(score)
    if include_musicxml:
        payload["musicxml"] = score_to_musicxml(score)
    return payload
