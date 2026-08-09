from __future__ import annotations

from app.engine.types import NoteEvent


def beats_per_bar(time_signature: tuple[int, int]) -> int:
    return time_signature[0]


def bar_duration_seconds(bpm: float, time_signature: tuple[int, int]) -> float:
    return beats_per_bar(time_signature) * (60.0 / bpm)


_DISTINCTIVE = frozenset({"yumba", "sincopa", "arrastre"})


def choose_rhythm_pair(profile: dict) -> tuple[str, str | None]:
    """Primary = home groove on the grid; secondary = optional colour blocks."""
    patterns = list(profile.get("rhythm_patterns") or ["marcato_en_cuatro"])
    primary = patterns[0]
    secondary = patterns[1] if len(patterns) > 1 else None
    # If a profile leads with a colour pattern, keep a steady marcato underneath
    if primary in _DISTINCTIVE:
        home = next((p for p in patterns if p.startswith("marcato")), None)
        secondary = primary
        primary = home or "marcato_en_dos"
    return primary, secondary


def choose_rhythm_pattern(profile: dict) -> str:
    """Backward-compatible: return primary home groove."""
    return choose_rhythm_pair(profile)[0]


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
    q = beat if beats_per_bar == 2 else bar_len / 2
    e = q / 2
    s = bar_len / 8  # sixteenth in 2/4

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
        # ♩.♪ ♪ ♪ on the 2/4 grid (no extra off-grid punches)
        d8 = beat * 0.75
        s16 = beat * 0.25
        e8 = beat * 0.5
        hit(0.0, d8 * 0.85, bass, 92)
        hit(d8, s16 * 0.85, fifth, 78)
        hit(beat, e8 * 0.75, root, 86)
        hit(beat + e8, e8 * 0.7, fifth if bar_index % 2 == 0 else third, 80)

    elif pattern == "milonga_332":
        # Accents on sixteenths 0, 3, 6 — exact 3+3+2 grid
        for off, pitch, vel in ((0, bass, 94), (3, fifth, 82), (6, root, 88)):
            hit(off * s, s * 2.0, pitch, vel)

    elif pattern == "vals_bass_chord":
        chord_mid = root
        chord_hi = fifth + 12
        hit(0.0, beat * 0.85, bass, 90)
        hit(0.0, beat * 0.55, bass + 12, 72)
        hit(beat, beat * 0.7, chord_mid, 68)
        hit(beat, beat * 0.7, chord_hi, 64)
        hit(beat * 2, beat * 0.65, chord_mid, 66)
        hit(beat * 2, beat * 0.65, third + 12, 62)

    elif pattern == "marcato_en_cuatro":
        vel = 96 if staccato == "high" else 88
        if beats_per_bar == 3:
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
        hit(0.0, q * 1.05, bass, 98)
        hit(0.0, q * 1.05, bass + 12, 90)
        if bar_index % 4 != 3:
            hit(q, q * 0.4, fifth, 72)

    elif pattern == "sincopa":
        # Biagi-ish hole: clear 1, silence on &, accent on beat 2 (grid-aligned)
        hit(0.0, e * 0.5, bass, 88)
        hit(e * 2, e * 0.85, fifth, 100)
        hit(e * 2, e * 0.85, root, 90)
        if bar_index % 2 == 0:
            hit(e * 3, e * 0.45, third, 76)

    elif pattern == "yumba":
        # Delayed weight after beat 1, then settle on beat 2 — still on 16th grid
        hit(0.0, s * 1.5, bass, 72)
        hit(s * 3, s * 3.5, root, 100)
        hit(s * 3, s * 3.5, fifth, 92)
        hit(e * 2, e * 0.7, bass, 84)

    elif pattern == "arrastre":
        # Drag into beat 2: light 1, swell into 2
        hit(0.0, e * 0.4, bass, 70)
        hit(e * 1, e * 0.5, bass, 78)
        hit(e * 2, e * 0.9, root, 96)
        hit(e * 2, e * 0.9, fifth, 88)

    elif pattern == "lyrical_phrasing":
        # On-beat sustains only (no mid-beat ghost hits that smear the pulse)
        hit(0.0, q * 0.95, bass, 76)
        hit(q, q * 0.9, root, 72)

    else:
        for i in range(max(beats_per_bar * 2, 4)):
            unit = bar_len / max(beats_per_bar * 2, 4)
            hit(i * unit, unit * 0.55, bass if i % 2 == 0 else fifth, 90)

    return notes
