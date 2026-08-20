"""Pass 3 — yeites / ornaments applied at render time (M4)."""

from __future__ import annotations

import random
from typing import Any

from app.engine.types import NoteEvent

# Re-use NCT labels on ornament note events via optional metadata dicts
# (NoteEvent itself stays pitch/time/vel/track; ornaments expand into NoteEvents).


def _tension_factor(drama: str, energy: float) -> float:
    base = {
        "climax": 1.35,
        "anticipate": 1.15,
        "rise": 1.1,
        "dense": 1.2,
        "normal": 1.0,
    }.get(drama or "normal", 1.0)
    return base * (0.75 + 0.5 * float(energy))


def decorate_melody_events(
    rng: random.Random,
    melody: list[dict[str, Any]],
    *,
    decoration: float,
    spb: float,
    dance_type: str,
    personality: str = "neutral",
    elaborations: dict[int, dict] | None = None,
    beats_per_bar: int = 2,
) -> list[NoteEvent]:
    """Expand skeleton melody into rendered RH notes with yeites.

    Called from the render layer — never mutates skeleton pitches as mandatory style.
    """
    notes: list[NoteEvent] = []
    elab_by_bar = elaborations or {}
    # Mugre only for dramatic personalities
    allow_mugre = personality in ("dramatic", "intense", "pugliese") or decoration >= 0.6

    for idx, m in enumerate(melody):
        if (m.get("voice") or "lead") == "ornament":
            continue
        start = float(m["start_beat"]) * spb
        dur = float(m["duration_beats"]) * spb
        pitch = int(m["pitch"])
        drama = str(m.get("drama") or "normal")
        energy = float(m.get("energy") or 0.5)
        phrase_end = bool(m.get("phrase_end"))
        bar = int(float(m["start_beat"]) // max(beats_per_bar, 1))
        elab = elab_by_bar.get(bar) or {}
        orn_boost = float(elab.get("ornament_boost") or 0)
        tension = _tension_factor(drama, energy)
        p = min(0.55, decoration * tension + orn_boost * 0.35)

        if dance_type == "vals":
            p *= 0.15
        elif dance_type == "milonga":
            p *= 0.55

        vel = 96 if (m.get("voice") or "lead") == "lead" else 72
        vel = int(vel * (0.75 + 0.45 * energy))
        if drama == "climax":
            vel = min(127, vel + 10)
        vel = min(127, vel)
        dur = max(0.05, dur)

        next_pitch = None
        if idx + 1 < len(melody):
            next_pitch = int(melody[idx + 1]["pitch"])

        used = False
        roll = rng.random()

        # Variación: rewrite quarter into 4 sixteenths on A_prime / high development
        if (
            not used
            and float(m["duration_beats"]) >= 0.9
            and float(m["duration_beats"]) <= 1.15
            and (m.get("section") in ("A_prime", "variacion") or int(m.get("motivic_development") or 0) >= 2)
            and roll < p * 0.35
        ):
            notes.extend(_variacion(pitch, start, dur, vel, next_pitch, rng))
            used = True

        # Arrastre before strong structural / climax
        elif (
            not used
            and m.get("structural_weight", 0) >= 1.0
            and drama in ("climax", "anticipate", "rise")
            and roll < p * 0.4
        ):
            notes.extend(_arrastre(pitch, start, dur, vel, rng))
            used = True

        # Apoyatura into long / phrase-end
        elif (
            not used
            and (phrase_end or float(m["duration_beats"]) >= 1.2)
            and roll < p * 0.5
        ):
            notes.extend(_apoyatura(pitch, start, dur, vel, rng))
            used = True

        # Mordente on long mid notes
        elif (
            not used
            and float(m["duration_beats"]) >= 1.0
            and not phrase_end
            and roll < p * 0.35
        ):
            notes.extend(_mordente(pitch, start, dur, vel, rng))
            used = True

        # Cromatismo when approaching by ≥3 descending
        elif (
            not used
            and next_pitch is not None
            and pitch - next_pitch >= 3
            and roll < p * 0.3
        ):
            notes.extend(_cromatismo(pitch, next_pitch, start, dur, vel, rng))
            used = True

        # Mugre — rare, dramatic only
        elif (
            not used
            and allow_mugre
            and drama == "climax"
            and roll < min(0.05, p * 0.08)
        ):
            notes.extend(_mugre(pitch, start, dur, vel))
            used = True

        if not used:
            notes.append(NoteEvent(pitch, start, dur, vel, "piano_rh"))

    return notes


def _apoyatura(
    pitch: int, start: float, dur: float, vel: int, rng: random.Random
) -> list[NoteEvent]:
    frac = rng.uniform(0.15, 0.30)
    grace_dur = dur * frac
    main_dur = dur - grace_dur
    grace = pitch + rng.choice([-2, -1, 1, 2])
    return [
        NoteEvent(grace, start, max(0.03, grace_dur), max(40, vel - 12), "piano_rh"),
        NoteEvent(pitch, start + grace_dur, max(0.05, main_dur), vel, "piano_rh"),
    ]


def _mordente(
    pitch: int, start: float, dur: float, vel: int, rng: random.Random
) -> list[NoteEvent]:
    total = min(dur * 0.3, dur * 0.28)
    third = total / 3
    nbr = pitch + rng.choice([-1, 1, -2, 2])
    return [
        NoteEvent(pitch, start, third, vel, "piano_rh"),
        NoteEvent(nbr, start + third, third, max(40, vel - 8), "piano_rh"),
        NoteEvent(pitch, start + 2 * third, max(0.05, dur - total), vel, "piano_rh"),
    ]


def _cromatismo(
    pitch: int,
    next_pitch: int,
    start: float,
    dur: float,
    vel: int,
    rng: random.Random,
) -> list[NoteEvent]:
    # Insert chromatic steps between pitch and a point toward next
    span = pitch - next_pitch
    n_steps = min(3, span)
    step_dur = dur / (n_steps + 1)
    out: list[NoteEvent] = []
    for i in range(n_steps):
        p = pitch - i
        out.append(NoteEvent(p, start + i * step_dur, step_dur * 0.95, vel - i, "piano_rh"))
    out.append(
        NoteEvent(
            pitch - n_steps,
            start + n_steps * step_dur,
            max(0.05, dur - n_steps * step_dur),
            vel,
            "piano_rh",
        )
    )
    return out


def _arrastre(
    pitch: int, start: float, dur: float, vel: int, rng: random.Random
) -> list[NoteEvent]:
    n = rng.choice([1, 2])
    grace_total = min(0.08 * n, dur * 0.25)
    each = grace_total / n
    out: list[NoteEvent] = []
    for i in range(n):
        p = pitch - (n - i)
        v = max(36, vel - 20 + i * 8)
        out.append(NoteEvent(p, start + i * each, each * 0.9, v, "piano_rh"))
    out.append(NoteEvent(pitch, start + grace_total, max(0.05, dur - grace_total), vel, "piano_rh"))
    return out


def _variacion(
    pitch: int,
    start: float,
    dur: float,
    vel: int,
    next_pitch: int | None,
    rng: random.Random,
) -> list[NoteEvent]:
    sixteenth = dur / 4
    pattern = rng.choice(
        [
            [0, 2, 4, 2],
            [0, -1, 0, 2],
            [0, 3, 5, 7],
            [0, 2, 0, -1],
        ]
    )
    out: list[NoteEvent] = []
    for i, off in enumerate(pattern):
        out.append(
            NoteEvent(
                pitch + off,
                start + i * sixteenth,
                sixteenth * 0.92,
                max(48, vel - (0 if i % 2 == 0 else 6)),
                "piano_rh",
            )
        )
    return out


def _mugre(pitch: int, start: float, dur: float, vel: int) -> list[NoteEvent]:
    return [
        NoteEvent(pitch, start, dur, vel, "piano_rh"),
        NoteEvent(pitch + 1, start, dur * 0.85, max(40, vel - 18), "piano_rh"),
    ]
