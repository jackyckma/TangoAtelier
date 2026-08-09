from __future__ import annotations

from app.engine.types import NoteEvent


def beats_per_bar(time_signature: tuple[int, int]) -> int:
    return time_signature[0]


def bar_duration_seconds(bpm: float, time_signature: tuple[int, int]) -> float:
    return beats_per_bar(time_signature) * (60.0 / bpm)


_PATTERN_PRIORITY = (
    "yumba",
    "sincopa",
    "arrastre",
    "pesante",
    "marcato_en_dos",
    "vals_bass_chord",
    "milonga_habanera",
    "milonga_332",
    "lyrical_phrasing",
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
    *,
    beats_per_bar: int = 2,
) -> list[NoteEvent]:
    """Generate LH piano notes for one bar. Patterns intentionally diverge by dance/orquesta."""
    root = chord_pitches[0] - 12
    fifth = (chord_pitches[2] if len(chord_pitches) > 2 else root + 7) - 12
    third = (chord_pitches[1] if len(chord_pitches) > 1 else root + 3) - 12
    bass = root - 12 if root >= 48 else root

    staccato = articulation.get("staccato_level", "medium")
    pause = articulation.get("pause_frequency", "low")

    notes: list[NoteEvent] = []
    beat = bar_len / max(beats_per_bar, 1)
    # In 2/4: quarter = beat, eighth = beat/2; keep aliases for tango patterns
    q = beat if beats_per_bar == 2 else bar_len / 2
    e = q / 2

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

    if pattern == "milonga_habanera":
        # Classic milonga/habanera in 2/4: ♩.♪ ♪ ♪  (dotted-8th + 16th + 8th + 8th)
        # Felt as "tum — ta tum tum" — earthy, driving, faster than tango.
        d8 = beat * 0.75
        s16 = beat * 0.25
        e8 = beat * 0.5
        hit(0.0, d8 * 0.85, bass, 92)
        hit(d8, s16 * 0.9, fifth, 78)
        hit(beat, e8 * 0.75, root, 86)
        hit(beat + e8, e8 * 0.7, fifth if bar_index % 2 == 0 else third, 80)
        # light chord punch on & of 2 occasionally
        if bar_index % 4 == 3:
            hit(beat + e8 * 0.5, e8 * 0.35, root + 12, 68)

    elif pattern == "milonga_332":
        # 3+3+2 in sixteenths within 2/4 (8 sixteenths): accents at 0, 3, 6
        s = bar_len / 8
        accents = (0, 3, 6)
        pitches = (bass, fifth, root)
        vels = (94, 82, 88)
        for off, pitch, vel in zip(accents, pitches, vels):
            hit(off * s, s * 2.2, pitch, vel)

    elif pattern == "vals_bass_chord":
        # Argentine vals: strong 1 (bass), lighter 2–3 (mid chords) — circular oom-pah-pah
        chord_mid = root
        chord_hi = fifth + 12
        hit(0.0, beat * 0.85, bass, 90)
        hit(0.0, beat * 0.55, bass + 12, 72)  # octave reinforce on 1
        hit(beat, beat * 0.7, chord_mid, 68)
        hit(beat, beat * 0.7, chord_hi, 64)
        hit(beat * 2, beat * 0.65, chord_mid, 66)
        hit(beat * 2, beat * 0.65, third + 12, 62)
        # occasional skipped beat 3 for breath (still vals, not tango silence)
        if pause == "high" and bar_index % 4 == 3:
            notes[:] = [n for n in notes if n.start < bar_start + beat * 2]

    elif pattern == "marcato_en_cuatro":
        vel = 96 if staccato == "high" else 88
        if beats_per_bar == 3:
            # fall back: mark each beat
            for i in range(3):
                hit(i * beat, beat * 0.45, bass if i == 0 else fifth, vel - i * 4)
        else:
            for i in range(4):
                pitch = bass if i % 2 == 0 else fifth
                hit(i * e, e * 0.55, pitch, vel - (4 if i % 2 else 0))

    elif pattern == "marcato_en_dos":
        dur = q * (0.7 if pause != "high" else 0.45)
        hit(0.0, dur, bass, 92)
        if pause == "high" and bar_index % 2 == 1:
            hit(q, q * 0.25, fifth, 70)
        else:
            hit(q, dur, fifth, 86)

    elif pattern == "pesante":
        hit(0.0, q * 1.1, bass, 98)
        hit(0.0, q * 1.1, bass + 12, 90)
        if bar_index % 4 != 3:
            hit(q, q * 0.35, fifth, 72)

    elif pattern in ("sincopa", "yumba", "arrastre"):
        hit(0.0, e * 0.5, bass, 88)
        if pattern == "yumba":
            hit(e * 1.35, e * 0.9, root, 100)
            hit(e * 1.35, e * 0.9, fifth, 92)
            hit(q + e * 0.2, e * 0.7, bass, 85)
        else:
            hit(e * 2.2, e * 0.7, fifth, 100)
            if bar_index % 2 == 0:
                hit(q + e, e * 0.5, root, 78)

    elif pattern == "lyrical_phrasing":
        # Soft sustained — used as tango lyrical, not as vals substitute
        hit(0.0, q * 0.9, bass, 78)
        hit(q * 0.5, e, fifth, 70)
        hit(q, q * 0.85, root, 74)

    else:
        for i in range(max(beats_per_bar * 2, 4)):
            unit = bar_len / max(beats_per_bar * 2, 4)
            hit(i * unit, unit * 0.55, bass if i % 2 == 0 else fifth, 90)

    return notes
