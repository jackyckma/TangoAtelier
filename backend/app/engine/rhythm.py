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


def _lh_tones(chord_pitches: list[int], prev_bass: int | None = None) -> tuple[int, int, int, int]:
    """Root / third / fifth in LH register + deep bass.

    When prev_bass is set, pick the bass octave that moves least (E6 voice leading).
    """
    root = chord_pitches[0] - 12
    fifth = (chord_pitches[2] if len(chord_pitches) > 2 else root + 7) - 12
    third = (chord_pitches[1] if len(chord_pitches) > 1 else root + 3) - 12
    bass = root - 12 if root >= 48 else root
    if prev_bass is not None:
        candidates = [c for c in (bass, bass + 12, bass - 12, bass + 24) if 28 <= c <= 52]
        if candidates:
            bass = min(candidates, key=lambda c: abs(c - prev_bass))
    return bass, root, third, fifth


def _safe_deep_bass(bass: int) -> int:
    deep = bass - 12
    return deep if deep >= 28 else bass


def _marcato_cuatro_pitches(bar_index: int, bass: int, root: int, third: int, fifth: int) -> list[int]:
    """Rotate LH pitch cells so marcato-en-4 isn't always bass–fifth–bass–fifth."""
    deep = _safe_deep_bass(bass)
    # Prefer motion: avoid identical consecutive hits inside a cell
    cells = (
        [bass, fifth, bass, fifth],
        [bass, third, fifth, third],
        [bass, fifth, root, fifth],
        [bass, fifth, third, root],
        [deep, fifth, bass, third],
        [bass, fifth, third, fifth],
    )
    return list(cells[bar_index % len(cells)])


def _marcato_dos_pitches(bar_index: int, bass: int, root: int, third: int, fifth: int) -> tuple[int, int]:
    deep = _safe_deep_bass(bass)
    # Second hit must differ from bass — when register collapses, fall back to fifth
    alt_root = root if root != bass else fifth
    alt_third = third if third != bass else fifth
    cells = (
        (bass, fifth),
        (bass, alt_root),
        (bass, alt_third),
        (deep, fifth),
        (bass, fifth + 12),
        (deep, alt_root),
    )
    return cells[bar_index % len(cells)]


def _block_bias(voicing_style: str, *, power: bool = False) -> float:
    """How often LH stacks pitches on one attack (block) vs arpeggiates (broken)."""
    base = {
        "octave_unison_bass": 0.82,
        "dense_dramatic": 0.75,
        "clear_dance_band": 0.55,
        "singing_legato": 0.48,
        "bright_staccato": 0.40,
    }.get(voicing_style, 0.5)
    return min(0.9, base + (0.2 if power else 0.0))


def left_hand_for_bar(
    pattern: str,
    bar_index: int,
    bar_start: float,
    bar_len: float,
    chord_pitches: list[int],
    articulation: dict,
    *,
    beats_per_bar: int = 2,
    voicing_style: str = "bright_staccato",
    power: bool = False,
    lh_upgrade: str | None = None,
    prev_bass: int | None = None,
) -> list[NoteEvent]:
    """Generate LH piano notes for one bar. Patterns intentionally diverge by dance/orquesta.

    lh_upgrade (A′ elaboration): 'walking' | 'busier' — richer accompaniment without
    changing the skeleton chord symbol.
    """
    bass, root, third, fifth = _lh_tones(chord_pitches, prev_bass=prev_bass)

    staccato = articulation.get("staccato_level", "medium")
    pause = articulation.get("pause_frequency", "low")
    # Deterministic mix — reference tango MIDI LH often ~half+ block onsets
    bias = _block_bias(voicing_style, power=power)
    if lh_upgrade == "walking":
        bias *= 0.35  # prefer broken / linear bass
    elif lh_upgrade == "busier":
        bias *= 0.55
    salt = sum(ord(c) for c in voicing_style) + (7 if power else 0)
    use_block = ((bar_index * 3 + salt) % 100) < int(bias * 100)

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

    def hit_block(start_off: float, dur: float, pitches: list[int], vel: int) -> None:
        """Bass/root on `piano_lh` (on time); upper tones on `piano_lh_chord` (may lag)."""
        if not pitches:
            return
        hit(start_off, dur, pitches[0], vel)
        for i, pitch in enumerate(pitches[1:]):
            notes.append(
                NoteEvent(
                    pitch=pitch,
                    start=bar_start + start_off,
                    duration=dur,
                    velocity=max(48, vel - (i + 1) * 6),
                    track="piano_lh_chord",
                )
            )

    # A′ walking: replace generic marcato with a clearer bass line (style patterns
    # like yumba/sincopa still run below, then we overlay connectors).
    walk_replace = lh_upgrade == "walking" and pattern in (
        "marcato_en_cuatro",
        "marcato_en_dos",
        "pesante",
        "lyrical_phrasing",
    )
    if walk_replace and beats_per_bar == 2:
        walk = [bass, third, fifth, root + 12]
        if bar_index % 2:
            walk = [bass, fifth, third, root + 12]
        for i, pitch in enumerate(walk):
            hit(i * e, e * 0.85, pitch, 88 - i * 4)
        if lh_upgrade:
            for n in notes:
                n.velocity = min(127, n.velocity + 6)
        return notes

    if walk_replace and beats_per_bar == 3:
        # Vals: bass – mid – mid+oct (still one-bar walk, not tango 16ths)
        mid = (third, fifth, root)[bar_index % 3]
        hit(0.0, beat * 0.85, bass, 90)
        hit(beat, beat * 0.7, mid, 74)
        hit(beat * 2, beat * 0.65, mid + 12 if mid < 60 else fifth, 70)
        for n in notes:
            n.velocity = min(127, n.velocity + 5)
        return notes

    if pattern == "milonga_habanera":
        # ♩.♪ ♪ ♪ on the 2/4 grid (no extra off-grid punches)
        d8 = beat * 0.75
        s16 = beat * 0.25
        e8 = beat * 0.5
        weak = (fifth, third, root, fifth + 12)[bar_index % 4]
        if use_block:
            hit_block(0.0, d8 * 0.85, [bass, bass + 12], 92)
        else:
            hit(0.0, d8 * 0.85, bass, 92)
        hit(d8, s16 * 0.85, fifth if bar_index % 2 == 0 else third, 78)
        hit(beat, e8 * 0.75, root if bar_index % 3 else bass + 12, 86)
        hit(beat + e8, e8 * 0.7, weak, 80)

    elif pattern == "milonga_332":
        # Accents on sixteenths 0, 3, 6 — exact 3+3+2 grid
        mid = (fifth, third, root)[bar_index % 3]
        if use_block:
            hit_block(0.0, s * 2.0, [bass, fifth], 94)
            hit(3 * s, s * 2.0, mid, 82)
            hit_block(6 * s, s * 2.0, [root, third], 88)
        else:
            for off, pitch, vel in ((0, bass, 94), (3, mid, 82), (6, root, 88)):
                hit(off * s, s * 2.0, pitch, vel)

    elif pattern == "vals_bass_chord":
        # Rotate mid-chord voicings so 1–2–3 isn't identical every bar
        chord_mid = (root, third, fifth)[bar_index % 3]
        chord_hi = (fifth + 12, third + 12, root + 12)[bar_index % 3]
        hit(0.0, beat * 0.85, bass, 90)
        if bar_index % 4 != 2:
            hit(0.0, beat * 0.55, bass + 12, 72)
        hit(beat, beat * 0.7, chord_mid, 68)
        hit(beat, beat * 0.7, chord_hi, 64)
        hit(beat * 2, beat * 0.65, chord_mid, 66)
        hit(beat * 2, beat * 0.65, (third + 12, fifth + 12, root + 12)[(bar_index + 1) % 3], 62)

    elif pattern == "marcato_en_cuatro":
        vel = 96 if staccato == "high" else 88
        pitches = _marcato_cuatro_pitches(bar_index, bass, root, third, fifth)
        if beats_per_bar == 3:
            for i in range(3):
                if use_block and i == 0:
                    hit_block(i * beat, beat * 0.45, [bass, fifth], vel)
                else:
                    hit(i * beat, beat * 0.45, pitches[i], vel - i * 4)
        else:
            # Micro-rhythm: every 4th bar lighten beat 2 (tango air) without losing grid
            skip_idx = 1 if bar_index % 4 == 3 else -1
            for i in range(4):
                if i == skip_idx:
                    continue
                # Strong beats: block / octave; weak beats: broken single
                if use_block and i % 2 == 0:
                    stack = [bass, fifth] if i == 0 else [root, third, fifth]
                    hit_block(i * e, e * 0.55, stack, vel)
                else:
                    hit(i * e, e * 0.55, pitches[i], vel - (4 if i % 2 else 0))

    elif pattern == "marcato_en_dos":
        dur = q * (0.7 if pause != "high" else 0.45)
        p0, p1 = _marcato_dos_pitches(bar_index, bass, root, third, fifth)
        if use_block:
            # Power: octave bass or LH shell on beat 1 (Di Sarli-ish weight)
            stack = (
                [p0, p0 + 12]
                if voicing_style == "octave_unison_bass"
                else [p0, root, fifth]
            )
            hit_block(0.0, dur, stack, 94)
        else:
            hit(0.0, dur, p0, 92)
        if pause == "high" and bar_index % 2 == 1:
            hit(q, q * 0.25, p1, 70)
        elif bar_index % 8 == 7:
            # Occasional hole on beat 2 — classic tango silence
            pass
        elif use_block and bar_index % 2 == 0:
            second = [p1, third] if p1 != third else [p1, fifth]
            hit_block(q, dur * 0.85, second, 84)
        else:
            hit(q, dur, p1, 86)

    elif pattern == "pesante":
        # Always a weighty block on 1 — this pattern's identity is power
        hit_block(0.0, q * 1.05, [bass, bass + 12, root], 98)
        if bar_index % 4 != 3:
            if use_block:
                hit_block(q, q * 0.4, [fifth, third], 74)
            else:
                hit(q, q * 0.4, (fifth, third, root)[bar_index % 3], 72)

    elif pattern == "sincopa":
        # Biagi-ish hole: clear 1, silence on &, accent on beat 2 (grid-aligned)
        hit(0.0, e * 0.5, bass, 88)
        if use_block:
            hit_block(
                e * 2,
                e * 0.85,
                [fifth, root] if bar_index % 2 == 0 else [root, third],
                100,
            )
        else:
            hit(e * 2, e * 0.85, fifth if bar_index % 2 == 0 else root, 100)
            hit(e * 2, e * 0.85, root if bar_index % 2 == 0 else third, 90)
        if bar_index % 2 == 0:
            hit(e * 3, e * 0.45, third, 76)

    elif pattern == "yumba":
        # Delayed weight after beat 1, then settle on beat 2 — still on 16th grid
        hit(0.0, s * 1.5, bass, 72)
        if use_block:
            hit_block(
                s * 3,
                s * 3.5,
                [root, fifth if bar_index % 2 == 0 else third],
                100,
            )
        else:
            hit(s * 3, s * 3.5, root, 100)
            hit(s * 3, s * 3.5, fifth if bar_index % 2 == 0 else third, 92)
        hit(e * 2, e * 0.7, bass if bar_index % 3 else fifth, 84)

    elif pattern == "arrastre":
        # Drag into beat 2: light 1, swell into 2
        hit(0.0, e * 0.4, bass, 70)
        hit(e * 1, e * 0.5, (bass, third, fifth)[bar_index % 3], 78)
        if use_block:
            hit_block(
                e * 2,
                e * 0.9,
                [root, fifth if bar_index % 2 == 0 else third],
                96,
            )
        else:
            hit(e * 2, e * 0.9, root, 96)
            hit(e * 2, e * 0.9, fifth if bar_index % 2 == 0 else third, 88)

    elif pattern == "lyrical_phrasing":
        # On-beat sustains; alternate bass/root so lyrical LH still moves
        p0, p1 = (bass, root) if bar_index % 2 == 0 else (bass, fifth)
        if use_block:
            hit_block(0.0, q * 0.95, [p0, p0 + 12], 76)
        else:
            hit(0.0, q * 0.95, p0, 76)
        hit(q, q * 0.9, p1, 72)

    else:
        pitches = _marcato_cuatro_pitches(bar_index, bass, root, third, fifth)
        n_hits = max(beats_per_bar * 2, 4)
        unit = bar_len / n_hits
        for i in range(n_hits):
            if use_block and i % 2 == 0:
                hit_block(i * unit, unit * 0.55, [pitches[i % 4], fifth], 90)
            else:
                hit(i * unit, unit * 0.55, pitches[i % 4], 90)

    # A′ busier: keep style identity, add a light connector + velocity lift
    if lh_upgrade == "busier" and beats_per_bar == 2 and notes:
        connector = third if abs(third - bass) <= 8 else fifth
        hit(e, e * 0.45, connector, 72)
        hit(e * 3, e * 0.4, root + 12 if root < 60 else fifth, 70)
    if lh_upgrade:
        for n in notes:
            n.velocity = min(127, int(n.velocity) + (8 if lh_upgrade == "busier" else 5))

    return notes
