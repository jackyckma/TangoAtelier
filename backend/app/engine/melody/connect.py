"""Pass 2 — connect structural tones with labeled NCTs; rests; phrase assembly (M4)."""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Any

from app.engine.melody.expectancy import (
    allow_dense_rhythm_cell,
    plan_rest_bars,
    prefer_breath_cell,
)
from app.engine.melody.nct import NCT
from app.engine.melody.rhythm_cell import RhythmCell, sample_rhythm_cell
from app.engine.melody.structural import (
    MELODY_HI,
    MELODY_LO,
    ChordSlot,
    StructuralNote,
    clamp_melody,
    chord_pool,
    nearest,
    plan_structural_line,
    scale_pool,
)

DENSITY_NOTES_PER_BAR = {
    "tango": {"low": 3, "medium": 5, "high": 7},
    "milonga": {"low": 3, "medium": 4, "high": 5},
    "vals": {"low": 2, "medium": 3, "high": 3},
}


@dataclass
class MelodyNote:
    pitch: int
    bar: int  # phrase-relative 0-based
    beat: float  # beat within bar
    duration: float
    nct: NCT
    structural_weight: float  # 1.0 structural, 0.0 connecting
    phrase_role: str = "question"
    phrase_end: bool = False


def _pc(p: int) -> int:
    return int(p) % 12


def _is_chord_tone(pitch: int, chord: ChordSlot) -> bool:
    pcs = {_pc(p) for p in chord_pool(chord.tonic, chord.mode, chord.symbol)}
    return _pc(pitch) in pcs


def plan_rests(
    phrase_bars: int,
    rng: random.Random,
    *,
    pause_frequency: str = "medium",
    drama_tag: str = "normal",
    energy: float = 0.5,
) -> set[int]:
    """Bars where melody leaves ≥1 beat of air — gated by drama expectancy."""
    return plan_rest_bars(
        phrase_bars,
        drama_tag=drama_tag,
        energy=energy,
        pause_frequency=pause_frequency,
        rng_pick_last=rng.random() < 0.5,
    )


def _recover_step(prev: int, leap_dir: int, scale: list[int]) -> int:
    want_dir = -1 if leap_dir > 0 else 1
    cands = [p for p in scale if 0 < (p - prev) * want_dir <= 2]
    if cands:
        return nearest(cands, prev + want_dir)
    return clamp_melody(prev + want_dir)


def connect(
    a: StructuralNote,
    b: StructuralNote,
    chord_a: ChordSlot,
    chord_b: ChordSlot,
    n_slots: int,
    rng: random.Random,
    *,
    leaps_ge7: int = 0,
    max_leaps_ge7: int = 2,
    allow_leap: bool = True,
) -> list[tuple[int, NCT]]:
    """Return n_slots of (pitch, nct) between structural a→b."""
    if n_slots <= 0:
        return []

    scale = sorted(
        set(scale_pool(chord_a.tonic, chord_a.mode) + scale_pool(chord_b.tonic, chord_b.mode))
    )
    pool_a = chord_pool(chord_a.tonic, chord_a.mode, chord_a.symbol)
    pool_b = chord_pool(chord_b.tonic, chord_b.mode, chord_b.symbol)
    dist = b.pitch - a.pitch
    adist = abs(dist)
    direction = 1 if dist > 0 else (-1 if dist < 0 else rng.choice([-1, 1]))

    out: list[tuple[int, NCT]] = []

    if adist == 0:
        # Mild declamación — at most one unison, prefer neighbor returns
        for i in range(n_slots):
            if i == 0 and rng.random() < 0.35:
                out.append((a.pitch, NCT.CHORD_TONE))
            else:
                nbr = clamp_melody(a.pitch + rng.choice([-2, -1, 1, 2]))
                out.append((nbr, NCT.NEIGHBOR))
                if i + 1 < n_slots:
                    out.append((a.pitch, NCT.CHORD_TONE))
                    break
        while len(out) < n_slots:
            step = clamp_melody((out[-1][0] if out else a.pitch) + rng.choice([-2, -1, 1, 2]))
            out.append((step, NCT.PASSING))
        return out[:n_slots]

    # Optional expressive leap + recovery when distance allows
    if (
        allow_leap
        and n_slots >= 2
        and leaps_ge7 < max_leaps_ge7
        and (
            (adist >= 5 and rng.random() < (0.7 if adist >= 7 else 0.5))
            or (adist >= 3 and n_slots >= 3 and rng.random() < 0.28)
        )
    ):
        leap_size = 7 if adist >= 7 and leaps_ge7 < max_leaps_ge7 else 5
        if adist >= 12 and rng.random() < 0.35:
            leap_size = 12
        leap_p = clamp_melody(a.pitch + direction * leap_size)
        # Prefer chord tone for leap landing when possible
        if not _is_chord_tone(leap_p, chord_a) and not _is_chord_tone(leap_p, chord_b):
            leap_p = nearest(pool_a + pool_b, leap_p)
        # Ensure actual leap ≥5
        if abs(leap_p - a.pitch) < 5:
            leap_p = clamp_melody(a.pitch + direction * 5)
        out.append((leap_p, NCT.CHORD_TONE if _is_chord_tone(leap_p, chord_a) else NCT.APPOGGIATURA))
        recover = _recover_step(leap_p, leap_p - a.pitch, scale)
        out.append((recover, NCT.PASSING))
        cur = recover
        while len(out) < n_slots:
            remaining = n_slots - len(out)
            step = max(1, abs(b.pitch - cur) // (remaining + 1))
            nxt = clamp_melody(cur + (1 if b.pitch >= cur else -1) * min(step, 2))
            nct = NCT.CHORD_TONE if _is_chord_tone(nxt, chord_b) else NCT.PASSING
            out.append((nxt, nct))
            cur = nxt
        return out[:n_slots]

    # Passing / chromatic descending
    cur = a.pitch
    for i in range(n_slots):
        remaining = n_slots - i
        delta = b.pitch - cur
        if delta == 0:
            nbr = clamp_melody(cur + rng.choice([-1, 1]))
            out.append((nbr, NCT.NEIGHBOR))
            cur = nbr
            continue
        dir_ = 1 if delta > 0 else -1
        # Chromatic only descending into chord tone
        if (
            dir_ < 0
            and abs(delta) >= 2
            and rng.random() < 0.4
            and remaining >= 1
        ):
            nxt = clamp_melody(cur - 1)
            if _is_chord_tone(nxt, chord_b) or _is_chord_tone(nxt, chord_a):
                out.append((nxt, NCT.PASSING))
            else:
                out.append((nxt, NCT.CHROMATIC))
            cur = nxt
            continue
        step = min(2, max(1, abs(delta) // (remaining + 1)))
        nxt = clamp_melody(cur + dir_ * step)
        # Keep motion stepwise unless filling a leap budget above
        if abs(nxt - cur) >= 5:
            nxt = clamp_melody(cur + dir_ * 2)
        nct = NCT.CHORD_TONE if _is_chord_tone(nxt, chord_a) or _is_chord_tone(nxt, chord_b) else NCT.PASSING
        out.append((nxt, nct))
        cur = nxt

    return out[:n_slots]


def _place_on_grid(
    pitches: list[tuple[int, NCT, float]],
    *,
    bar: int,
    beats_per_bar: float,
    cell: RhythmCell,
    leave_rest: bool,
    dance_type: str,
) -> list[MelodyNote]:
    """Place pitches onto rhythm-cell onsets; durations fill to next onset (sung line)."""
    if not pitches:
        return []

    if dance_type == "vals":
        base_onsets = [0.0, 1.0, 2.0]
    elif dance_type == "milonga":
        base_onsets = [o for o in cell.onsets if 0 <= o < beats_per_bar] or [0.0, 0.75, 1.5]
    else:
        base_onsets = [o for o in cell.onsets if 0 <= o < beats_per_bar] or [0.0, 0.5, 1.0, 1.5]

    # Prefer matching cell size; if denser, extend with eighth/16th grid by density need
    onsets = list(base_onsets)
    if len(pitches) > len(onsets):
        if dance_type == "vals":
            step = 1.0
        elif len(pitches) >= int(beats_per_bar * 2.5):
            step = 0.25  # need >4 attacks in 2/4
        else:
            step = 0.5
        t = 0.0
        extra: list[float] = []
        while t < beats_per_bar - 0.01 and len(onsets) + len(extra) < len(pitches):
            if all(abs(t - o) > 0.05 for o in onsets):
                extra.append(t)
            t += step
        onsets = sorted(onsets + extra)[: len(pitches)]

    n = min(len(pitches), len(onsets))
    onsets = onsets[:n]
    pitches = pitches[:n]

    # End boundary — leave ≥1 beat rest when requested
    bar_end = beats_per_bar - (1.0 if leave_rest else 0.0)
    if bar_end <= 0.5:
        bar_end = beats_per_bar * 0.5

    notes: list[MelodyNote] = []
    for i, ((pitch, nct, weight), onset) in enumerate(zip(pitches, onsets)):
        if onset >= bar_end:
            continue
        next_onset = onsets[i + 1] if i + 1 < len(onsets) else bar_end
        gap = max(0.25, next_onset - onset)
        # Sing through the gap; structural / breath cells hold longer
        if weight >= 1.0 and cell.id in (
            "held",
            "long_short",
            "vals_held",
            "vals_long",
            "milonga_held",
            "milonga_long_short",
        ):
            dur = min(gap, max(1.5, gap * 0.95))
        elif weight >= 1.0:
            dur = min(gap, max(1.0, gap * 0.9))
        elif dance_type == "vals":
            dur = min(gap * 0.98, max(0.85, gap * 0.9))
        else:
            # Bias toward quarter values when gap allows
            if gap >= 1.0:
                dur = min(gap * 0.92, max(0.75, gap * 0.85))
            else:
                dur = min(gap * 0.92, max(0.45, gap * 0.8))
        dur = min(dur, bar_end - onset)
        if dur < 0.35:
            dur = min(0.45, bar_end - onset)
        if dur < 0.25:
            continue
        notes.append(
            MelodyNote(
                pitch=clamp_melody(pitch),
                bar=bar,
                beat=round(float(onset), 4),
                duration=round(float(dur), 4),
                nct=nct,
                structural_weight=weight,
            )
        )
    return notes


def generate_phrase_melody(
    rng: random.Random,
    *,
    phrase_bars: int,
    cadence: str,
    chords: list[ChordSlot],
    dance_type: str,
    density: str,
    beats_per_bar: float,
    prev_end: int | None,
    register_bias: int = 0,
    prefer_contour: str | None = None,
    pitch_cell_intervals: list[int] | None = None,
    rhythm_cells: list[RhythmCell] | None = None,
    pause_frequency: str = "medium",
    phrase_role_question_bars: int | None = None,
    drama_tag: str = "normal",
    energy: float = 0.5,
) -> tuple[list[MelodyNote], int]:
    """Pass 1+2 for one phrase. Returns (notes, last_pitch)."""
    phrase_obj = type("Phrase", (), {"bars": phrase_bars, "cadence": cadence})()
    structural = plan_structural_line(
        phrase_obj,
        chords,
        dance_type=dance_type,
        prev_end=prev_end,
        rng=rng,
        beats_per_bar=beats_per_bar,
        register_bias=register_bias,
        prefer_contour=prefer_contour,
        pitch_cell_intervals=pitch_cell_intervals,
    )

    rest_bars = plan_rests(
        phrase_bars,
        rng,
        pause_frequency=pause_frequency,
        drama_tag=drama_tag,
        energy=energy,
    )
    target_npb = float(
        DENSITY_NOTES_PER_BAR.get(dance_type, DENSITY_NOTES_PER_BAR["tango"]).get(density, 5)
    )
    # Stable emotion: do not chase the high density target with connecting spray
    if drama_tag in ("normal", "release", "pause") and density == "high":
        target_npb = min(
            target_npb,
            float(
                DENSITY_NOTES_PER_BAR.get(dance_type, DENSITY_NOTES_PER_BAR["tango"]).get(
                    "medium", 5
                )
            ),
        )
    # Density over the full phrase — rest bars still carry a short note + gap, not silence-only
    target_total = max(len(structural) + 1, int(round(target_npb * phrase_bars)))
    if dance_type == "vals":
        target_total = min(target_total, phrase_bars * 3)
    elif dance_type == "milonga":
        target_total = min(target_total, phrase_bars * 5)

    n_connect = max(0, target_total - len(structural))
    n_gaps = max(1, len(structural) - 1)
    fills = [n_connect // n_gaps] * n_gaps
    for i in range(n_connect % n_gaps):
        fills[i] += 1

    cells = list(rhythm_cells) if rhythm_cells else [sample_rhythm_cell(rng, dance_type) for _ in range(3)]
    # Ensure breath cells available
    breath_ids = {"held", "long_short", "vals_held", "vals_long", "milonga_held", "milonga_long_short"}
    if not any(c.id in breath_ids for c in cells):
        cells.append(sample_rhythm_cell(rng, dance_type))

    # Timeline of absolute events as (time, pitch, nct, weight)
    events: list[tuple[float, int, NCT, float]] = []
    leaps_ge7 = 0
    q_cut = phrase_role_question_bars if phrase_role_question_bars is not None else (phrase_bars + 1) // 2

    for i, sn in enumerate(structural):
        t = sn.bar * beats_per_bar + sn.beat
        events.append((t, sn.pitch, NCT.CHORD_TONE, 1.0))
        if i + 1 >= len(structural):
            break
        nxt = structural[i + 1]
        chord_i = chords[min(sn.bar, len(chords) - 1)]
        chord_j = chords[min(nxt.bar, len(chords) - 1)]
        # Encourage leaps on leap_fill / when contour prefers
        allow_leap = True
        filled = connect(
            sn,
            nxt,
            chord_i,
            chord_j,
            fills[i],
            rng,
            leaps_ge7=leaps_ge7,
            max_leaps_ge7=2,
            allow_leap=allow_leap,
        )
        a_t = sn.bar * beats_per_bar + sn.beat
        b_t = nxt.bar * beats_per_bar + nxt.beat
        if b_t <= a_t:
            b_t = a_t + 0.5
        for k, (p, nct) in enumerate(filled):
            frac = (k + 1) / (len(filled) + 1)
            et = a_t + (b_t - a_t) * frac
            events.append((et, p, nct, 0.0))
            if events and len(events) >= 2:
                iv = events[-1][1] - events[-2][1]
                if abs(iv) >= 7:
                    leaps_ge7 += 1

    events.sort(key=lambda e: e[0])

    # Bucket into bars and apply rhythm cells
    by_bar: dict[int, list[tuple[int, NCT, float]]] = {b: [] for b in range(phrase_bars)}
    for t, p, nct, w in events:
        bar = int(t // beats_per_bar)
        bar = max(0, min(phrase_bars - 1, bar))
        # Strong-beat NCT constraint
        beat = t - bar * beats_per_bar
        strong = beat < 0.08 or abs(beat - beats_per_bar / 2) < 0.08 or (
            beats_per_bar >= 2.9 and abs(beat - 1.0) < 0.08
        )
        if strong and nct not in (NCT.CHORD_TONE, NCT.APPOGGIATURA, NCT.SUSPENSION) and w < 1.0:
            pool = chord_pool(
                chords[min(bar, len(chords) - 1)].tonic,
                chords[min(bar, len(chords) - 1)].mode,
                chords[min(bar, len(chords) - 1)].symbol,
            )
            p = nearest(pool, p)
            nct = NCT.CHORD_TONE
        by_bar[bar].append((clamp_melody(p), nct, w))

    reshaped: list[MelodyNote] = []
    for bar in range(phrase_bars):
        material = by_bar.get(bar) or []
        leave_rest = bar in rest_bars
        if not material:
            continue
        # Pick rhythm cell — expectancy: breath on stable / rest; dense only on drive
        has_struct = any(w >= 1.0 for _, _, w in material)
        want_breath = prefer_breath_cell(
            drama_tag, leave_rest=leave_rest, material_count=len(material)
        ) or (bar == phrase_bars - 1 and has_struct)
        if want_breath:
            breath = [c for c in cells if c.id in breath_ids] or cells
            cell = breath[bar % len(breath)]
            if leave_rest and len(material) > 3:
                structs = [m for m in material if m[2] >= 1.0]
                others = [m for m in material if m[2] < 1.0]
                material = (structs[:1] + others)[: max(2, min(3, len(material)))]
        else:
            cell = cells[bar % len(cells)]
            if len(material) >= 4 and allow_dense_rhythm_cell(drama_tag, density):
                dense = [c for c in cells if len(c.onsets) >= 3] or cells
                cell = dense[bar % len(dense)]
            elif len(material) >= 4:
                # Cap material instead of spraying 16ths on a stable line
                structs = [m for m in material if m[2] >= 1.0]
                others = [m for m in material if m[2] < 1.0]
                material = (structs + others)[: max(2, min(3, len(material)))]
                breath = [c for c in cells if c.id in breath_ids] or cells
                cell = breath[bar % len(breath)]

        placed = _place_on_grid(
            material,
            bar=bar,
            beats_per_bar=beats_per_bar,
            cell=cell,
            leave_rest=leave_rest,
            dance_type=dance_type,
        )
        for n in placed:
            n.phrase_role = "answer" if n.bar >= q_cut else "question"
        reshaped.extend(placed)

    if not reshaped:
        sn = structural[-1]
        reshaped = [
            MelodyNote(
                pitch=sn.pitch,
                bar=sn.bar,
                beat=0.0,
                duration=min(1.5, beats_per_bar),
                nct=NCT.CHORD_TONE,
                structural_weight=1.0,
                phrase_role="answer",
                phrase_end=True,
            )
        ]

    reshaped.sort(key=lambda n: (n.bar, n.beat))

    # Trim durations so notes never overlap (keep pitches; preserve recovery tones)
    for i in range(len(reshaped) - 1):
        a, b = reshaped[i], reshaped[i + 1]
        a_start = a.bar * beats_per_bar + a.beat
        b_start = b.bar * beats_per_bar + b.beat
        max_dur = b_start - a_start - 0.02
        if max_dur < 0.2:
            # Nearly simultaneous — nudge b forward slightly
            b.beat = min(beats_per_bar - 0.25, a.beat + 0.25)
            if b.beat <= a.beat and b.bar == a.bar:
                b.bar = min(phrase_bars - 1, a.bar + 1)
                b.beat = 0.0
            b_start = b.bar * beats_per_bar + b.beat
            max_dur = max(0.25, b_start - a_start - 0.02)
        if a.structural_weight >= 1.0 and max_dur >= 1.5:
            a.duration = min(max(a.duration, 1.5), max_dur)
        else:
            a.duration = min(a.duration, max_dur)
            a.duration = max(0.35, a.duration)

    # Density top-up on free eighth slots (non-overlapping)
    # Continuity: do not invent rapid fillers on stable / rising lines
    allow_topup = drama_tag in ("climax", "dense") or (
        drama_tag == "rise" and density == "high"
    )
    if allow_topup and len(reshaped) < target_total * 0.85:
        scale = scale_pool(chords[0].tonic, chords[0].mode)
        step = 1.0 if dance_type == "vals" else 0.5
        guard = 0
        while len(reshaped) < int(target_total * 0.9) and guard < 300:
            guard += 1
            bar = rng.randrange(phrase_bars)
            if bar in rest_bars and sum(1 for n in reshaped if n.bar == bar) >= 2:
                continue
            occupied = sorted(
                (n.beat, n.beat + n.duration) for n in reshaped if n.bar == bar
            )
            beat = 0.0
            placed = False
            limit = beats_per_bar - (1.0 if bar in rest_bars else 0.0)
            while beat < limit - 0.3:
                overlaps = any(s - 0.02 < beat < e for s, e in occupied)
                if not overlaps:
                    neighbors = [n for n in reshaped if n.bar == bar] or reshaped
                    prev = min(
                        neighbors,
                        key=lambda n: abs(
                            (n.bar * beats_per_bar + n.beat) - (bar * beats_per_bar + beat)
                        ),
                    )
                    # Keep filler stepwise — never leap from filler (avoids unrecovered leaps)
                    cands = [p for p in scale if 0 < abs(p - prev.pitch) <= 2] or [prev.pitch]
                    pitch = rng.choice(cands)
                    # Duration until next occupied or limit
                    next_occ = limit
                    for s, e in occupied:
                        if s > beat:
                            next_occ = min(next_occ, s)
                            break
                    dur = min(0.5 if dance_type != "vals" else 0.9, next_occ - beat - 0.02)
                    if dur >= 0.35:
                        reshaped.append(
                            MelodyNote(
                                pitch=clamp_melody(pitch),
                                bar=bar,
                                beat=round(beat, 4),
                                duration=round(dur, 4),
                                nct=NCT.PASSING,
                                structural_weight=0.0,
                                phrase_role="answer" if bar >= q_cut else "question",
                            )
                        )
                        placed = True
                        break
                beat += step
            if not placed:
                # try another bar
                continue
            reshaped.sort(key=lambda n: (n.bar, n.beat))

    reshaped.sort(key=lambda n: (n.bar, n.beat))

    # Leap recovery: fix unrecovered leaps in place
    for i in range(len(reshaped) - 2):
        a, b, c = reshaped[i], reshaped[i + 1], reshaped[i + 2]
        iv = b.pitch - a.pitch
        if abs(iv) < 5:
            continue
        step = c.pitch - b.pitch
        if (iv > 0 and step >= 0) or (iv < 0 and step <= 0):
            scale = scale_pool(
                chords[min(b.bar, len(chords) - 1)].tonic,
                chords[min(b.bar, len(chords) - 1)].mode,
            )
            c.pitch = _recover_step(b.pitch, iv, scale)
            c.nct = NCT.PASSING
    # Trailing leap into last note: insert recovery if needed
    if len(reshaped) >= 2:
        a, b = reshaped[-2], reshaped[-1]
        iv = b.pitch - a.pitch
        if abs(iv) >= 5 and b.structural_weight < 1.0:
            scale = scale_pool(
                chords[min(a.bar, len(chords) - 1)].tonic,
                chords[min(a.bar, len(chords) - 1)].mode,
            )
            b.pitch = _recover_step(a.pitch, iv, scale)
            b.nct = NCT.PASSING

    _ensure_phrase_rest(reshaped, phrase_bars, beats_per_bar, rest_bars)

    # Guarantee ≥1 long note without destroying density: elongate a structural on a quiet bar
    if not any(n.duration >= 1.5 for n in reshaped):
        by_bar_count: dict[int, int] = {}
        for n in reshaped:
            by_bar_count[n.bar] = by_bar_count.get(n.bar, 0) + 1
        candidates = [n for n in reshaped if n.structural_weight >= 1.0] or list(reshaped)
        candidates.sort(key=lambda n: (by_bar_count.get(n.bar, 99), n.beat))
        for n in candidates:
            # Remove other notes in same bar after this one to make room
            keep = []
            for x in reshaped:
                if x.bar == n.bar and x is not n and x.beat >= n.beat:
                    continue
                keep.append(x)
            room = beats_per_bar - n.beat
            if n.bar in rest_bars:
                room = min(room, max(0.0, beats_per_bar - 1.0 - n.beat))
            if room >= 1.5:
                n.duration = 1.5
                reshaped = keep
                if n not in reshaped:
                    reshaped.append(n)
                reshaped.sort(key=lambda x: (x.bar, x.beat))
                break

    # Soft density cap
    if len(reshaped) > target_total * 1.3:
        scored = sorted(
            enumerate(reshaped),
            key=lambda iv: (iv[1].structural_weight, iv[1].duration, -iv[0]),
        )
        drop = set()
        excess = len(reshaped) - int(target_total * 1.2)
        for idx, n in scored:
            if excess <= 0:
                break
            if n.structural_weight >= 1.0 or n.phrase_end:
                continue
            drop.add(idx)
            excess -= 1
        reshaped = [n for i, n in enumerate(reshaped) if i not in drop]

    if reshaped:
        for n in reshaped:
            n.phrase_end = False
        reshaped[-1].phrase_end = True
        reshaped[-1].phrase_role = "answer"
        room = beats_per_bar - reshaped[-1].beat
        if reshaped[-1].duration < 1.0 and room >= 1.0:
            reshaped[-1].duration = min(room, max(1.0, reshaped[-1].duration))

    for n in reshaped:
        n.pitch = clamp_melody(n.pitch)

    # Final leap sweep after density edits
    for i in range(len(reshaped) - 2):
        a, b, c = reshaped[i], reshaped[i + 1], reshaped[i + 2]
        iv = b.pitch - a.pitch
        if abs(iv) < 5:
            continue
        step = c.pitch - b.pitch
        if (iv > 0 and step >= 0) or (iv < 0 and step <= 0):
            scale = scale_pool(
                chords[min(b.bar, len(chords) - 1)].tonic,
                chords[min(b.bar, len(chords) - 1)].mode,
            )
            c.pitch = _recover_step(b.pitch, iv, scale)
            c.nct = NCT.PASSING

    _ensure_phrase_rest(reshaped, phrase_bars, beats_per_bar, rest_bars)

    last = reshaped[-1].pitch if reshaped else (prev_end or 72)
    return reshaped, int(last)



def _ensure_phrase_rest(
    notes: list[MelodyNote],
    phrase_bars: int,
    beats_per_bar: float,
    rest_bars: set[int],
) -> None:
    if not notes:
        return
    end_phrase = phrase_bars * beats_per_bar

    def _has_rest(ns: list[MelodyNote]) -> bool:
        times = sorted((n.bar * beats_per_bar + n.beat, n.duration) for n in ns)
        for i, (t, d) in enumerate(times):
            nxt = times[i + 1][0] if i + 1 < len(times) else end_phrase
            if nxt - (t + d) >= 1.0 - 1e-6:
                return True
        return False

    if _has_rest(notes):
        return

    target_bar = next(iter(rest_bars), max(0, phrase_bars // 2))
    gap_start = target_bar * beats_per_bar + max(0.0, beats_per_bar - 1.0)
    gap_end = gap_start + 1.0

    for n in notes:
        abs_t = n.bar * beats_per_bar + n.beat
        if abs_t < gap_start <= abs_t + n.duration:
            n.duration = max(0.25, gap_start - abs_t)

    notes[:] = [
        n
        for n in notes
        if not (gap_start <= n.bar * beats_per_bar + n.beat < gap_end)
    ]

    if _has_rest(notes):
        return

    if notes:
        notes.sort(key=lambda n: (n.bar, n.beat))
        last = notes[-1]
        abs_t = last.bar * beats_per_bar + last.beat
        last.duration = max(0.25, min(last.duration, end_phrase - 1.0 - abs_t))



def melody_notes_to_dicts(
    notes: list[MelodyNote],
    *,
    start_bar: int,
    beats_per_bar: float,
    voice: str = "lead",
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for n in notes:
        d: dict[str, Any] = {
            "pitch": int(n.pitch),
            "start_beat": round((start_bar + n.bar) * beats_per_bar + n.beat, 3),
            "duration_beats": round(max(0.08, n.duration), 3),
            "phrase_role": n.phrase_role,
            "voice": voice,
            "nct": n.nct.value if isinstance(n.nct, NCT) else str(n.nct),
            "structural_weight": float(n.structural_weight),
        }
        if n.phrase_end:
            d["phrase_end"] = True
        out.append(d)
    return out
