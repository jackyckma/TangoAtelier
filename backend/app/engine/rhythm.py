from __future__ import annotations

from app.engine.types import NoteEvent


def beats_per_bar(time_signature: tuple[int, int]) -> int:
    return time_signature[0]


def bar_duration_seconds(bpm: float, time_signature: tuple[int, int]) -> float:
    # In 2/4, two quarter-note beats per bar
    return beats_per_bar(time_signature) * (60.0 / bpm)


_PATTERN_PRIORITY = (
    "yumba",
    "sincopa",
    "arrastre",
    "pesante",
    "marcato_en_dos",
    "lyrical_phrasing",
    "milonga_habanera",
    "marcato_en_cuatro",
)


def choose_rhythm_pattern(profile: dict) -> str:
    """Prefer the most distinctive listed pattern so orquestas diverge clearly."""
    patterns = profile.get("rhythm_patterns") or ["marcato_en_cuatro"]
    ranked = sorted(
        patterns,
        key=lambda p: _PATTERN_PRIORITY.index(p)
        if p in _PATTERN_PRIORITY
        else 99,
    )
    return ranked[0]


def left_hand_for_bar(
    pattern: str,
    bar_index: int,
    bar_start: float,
    bar_len: float,
    chord_pitches: list[int],
    articulation: dict,
) -> list[NoteEvent]:
    """Generate LH piano notes for one bar. Patterns intentionally diverge by orquesta."""
    root = chord_pitches[0] - 12  # octave below
    fifth = (chord_pitches[2] if len(chord_pitches) > 2 else root + 7) - 12
    bass = root - 12 if root >= 48 else root

    staccato = articulation.get("staccato_level", "medium")
    pause = articulation.get("pause_frequency", "low")

    notes: list[NoteEvent] = []
    q = bar_len / 2  # quarter in 2/4
    e = bar_len / 4  # eighth

    def hit(start_off: float, dur: float, pitch: int, vel: int) -> None:
        notes.append(
            NoteEvent(
                pitch=pitch,
                start=bar_start + start_off,
                duration=dur,
                velocity=vel,
                track="piano_lh",
            )
        )

    if pattern == "marcato_en_cuatro":
        # Every eighth strongly — D'Arienzo heartbeat
        vel = 96 if staccato == "high" else 88
        for i in range(4):
            pitch = bass if i % 2 == 0 else fifth
            hit(i * e, e * 0.55, pitch, vel - (4 if i % 2 else 0))

    elif pattern == "marcato_en_dos":
        # Beats 1 and 2 only, heavier, with space — Di Sarli / Canaro
        dur = q * (0.7 if pause != "high" else 0.45)
        hit(0.0, dur, bass, 92)
        if pause == "high" and bar_index % 2 == 1:
            # leave second beat almost empty periodically
            hit(q, q * 0.25, fifth, 70)
        else:
            hit(q, dur, fifth, 86)

    elif pattern == "pesante":
        # Thick octave bass on beat 1, long sustain, sparse beat 2
        hit(0.0, q * 1.1, bass, 98)
        hit(0.0, q * 1.1, bass + 12, 90)
        if bar_index % 4 != 3:
            hit(q, q * 0.35, fifth, 72)

    elif pattern in ("sincopa", "yumba", "arrastre"):
        # Delayed / offbeat accent — Biagi gap or Pugliese drag
        hit(0.0, e * 0.5, bass, 88)
        # intentional gap
        if pattern == "yumba":
            # late heavy chordal punch near end of beat 1
            hit(e * 1.35, e * 0.9, root, 100)
            hit(e * 1.35, e * 0.9, fifth, 92)
            hit(q + e * 0.2, e * 0.7, bass, 85)
        else:
            # Biagi: sudden hole then accent
            hit(e * 2.2, e * 0.7, fifth, 100)
            if bar_index % 2 == 0:
                hit(q + e, e * 0.5, root, 78)

    elif pattern in ("lyrical_phrasing", "milonga_habanera"):
        # Softer, more sustained
        hit(0.0, q * 0.9, bass, 78)
        hit(q * 0.5, e, fifth, 70)
        hit(q, q * 0.85, root, 74)

    else:
        # default marcato cuatro
        for i in range(4):
            hit(i * e, e * 0.55, bass if i % 2 == 0 else fifth, 90)

    return notes
