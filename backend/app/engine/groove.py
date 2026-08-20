"""M10 — Pulse / groove rendering helpers.

Skeleton supplies groove_role intent; this module resolves style-profile pulse
params and executes pattern runs + microtiming / accent / humanize at render.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.engine.types import NoteEvent

SECTION_GROOVE_ROLES: dict[str, str] = {
    "intro": "home",
    "A": "home",
    "bridge": "pivot",
    "B": "contrast_drive",
    "A_prime": "home_elevated",
    "variacion": "contrast_drive",
    "coda": "home_cadence",
}


@dataclass(frozen=True)
class PulseParams:
    feel: str = "drive"  # drive | heart | dramatic
    beat1_weight: float = 1.05
    other_beat_weight: float = 0.92
    bass_on_time: bool = True
    chord_lag_ms: float = 0.0
    humanize_ms: float = 18.0
    staccato_bias: float = 0.55
    silence_bias: float = 0.12
    colour_aggression: float = 0.25


_PULSE_BY_ID: dict[str, PulseParams] = {
    "simple": PulseParams(
        feel="drive", chord_lag_ms=0.0, beat1_weight=1.05, other_beat_weight=0.92,
        silence_bias=0.08, humanize_ms=18.0, staccato_bias=0.55, colour_aggression=0.15,
    ),
    "d_arienzo": PulseParams(
        feel="drive", chord_lag_ms=4.0, beat1_weight=1.05, other_beat_weight=0.90,
        silence_bias=0.08, humanize_ms=18.0, staccato_bias=0.55, colour_aggression=0.30,
    ),
    "di_sarli": PulseParams(
        feel="heart", chord_lag_ms=22.0, beat1_weight=1.20, other_beat_weight=0.95,
        silence_bias=0.16, humanize_ms=20.0, staccato_bias=0.35, colour_aggression=0.20,
    ),
    "pugliese": PulseParams(
        feel="dramatic", chord_lag_ms=36.0, beat1_weight=1.25, other_beat_weight=0.95,
        silence_bias=0.22, humanize_ms=22.0, staccato_bias=0.45, colour_aggression=0.40,
    ),
    "troilo": PulseParams(
        feel="heart", chord_lag_ms=16.0, beat1_weight=1.12, other_beat_weight=0.93,
        silence_bias=0.14, humanize_ms=20.0, staccato_bias=0.40, colour_aggression=0.22,
    ),
    "canaro": PulseParams(
        feel="drive", chord_lag_ms=8.0, beat1_weight=1.08, other_beat_weight=0.92,
        silence_bias=0.10, humanize_ms=18.0, staccato_bias=0.50, colour_aggression=0.22,
    ),
    "biagi": PulseParams(
        feel="drive", chord_lag_ms=6.0, beat1_weight=1.10, other_beat_weight=0.90,
        silence_bias=0.18, humanize_ms=18.0, staccato_bias=0.60, colour_aggression=0.35,
    ),
}

_DEFAULT_PULSE = PulseParams()


def resolve_pulse(profile: dict[str, Any]) -> PulseParams:
    base = _PULSE_BY_ID.get(str(profile.get("id") or ""), _DEFAULT_PULSE)
    raw = profile.get("pulse")
    if not isinstance(raw, dict) or not raw:
        return base
    return PulseParams(
        feel=str(raw.get("feel", base.feel)),
        beat1_weight=float(raw.get("beat1_weight", base.beat1_weight)),
        other_beat_weight=float(raw.get("other_beat_weight", base.other_beat_weight)),
        bass_on_time=bool(raw.get("bass_on_time", base.bass_on_time)),
        chord_lag_ms=float(raw.get("chord_lag_ms", base.chord_lag_ms)),
        humanize_ms=float(raw.get("humanize_ms", base.humanize_ms)),
        staccato_bias=float(raw.get("staccato_bias", base.staccato_bias)),
        silence_bias=float(raw.get("silence_bias", base.silence_bias)),
        colour_aggression=float(raw.get("colour_aggression", base.colour_aggression)),
    )


def chord_lag_ms_to_beats(chord_lag_ms: float, bpm: float) -> float:
    if bpm <= 0 or chord_lag_ms <= 0:
        return 0.0
    return (chord_lag_ms / 1000.0) * (bpm / 60.0)


def chord_lag_seconds(pulse: PulseParams) -> float:
    return max(0.0, pulse.chord_lag_ms) / 1000.0


def accent_multiplier(beat_index: int, pulse: PulseParams) -> float:
    if beat_index <= 0:
        return pulse.beat1_weight
    return pulse.other_beat_weight


def drive_colour_pattern(
    primary: str,
    secondary: str | None,
    extras: list[str] | None,
    dance_type: str,
) -> str:
    colour = [
        p for p in ((secondary,) if secondary else ()) + tuple(extras or ())
        if p and p != primary
    ]
    if dance_type == "milonga":
        if "milonga_332" in colour:
            return "milonga_332"
        return colour[0] if colour else "milonga_332"
    if dance_type == "vals":
        return colour[0] if colour else primary
    if secondary and secondary != primary:
        return secondary
    if colour:
        return colour[0]
    return "milonga_332"


def pattern_for_groove_bar(
    primary: str,
    secondary: str | None,
    bar: int,
    *,
    extras: list[str] | None = None,
    groove: dict[str, Any] | None = None,
    dance_type: str = "tango",
) -> str:
    """Map section groove_role → pattern with continuous contrast runs."""
    intent = groove or {}
    role = str(intent.get("groove_role") or "")
    colour = drive_colour_pattern(primary, secondary, extras, dance_type)

    if not role:
        return _legacy_colour_slots(primary, secondary, bar, extras=extras, groove=intent)

    local = int(intent.get("section_local_bar", 0))
    section_bars = max(1, int(intent.get("section_bars") or 8))
    force_home = bool(intent.get("force_primary"))

    if role in ("home", "home_elevated", "home_cadence"):
        if force_home or colour == primary or dance_type == "vals":
            return primary
        phrase_len = 4 if dance_type != "vals" else 3
        at_phrase_end = (local % phrase_len) == (phrase_len - 1)
        slots = intent.get("colour_slots")
        if at_phrase_end and slots and (local % 8) in {int(s) for s in slots}:
            return colour
        return primary

    if role == "pivot":
        if not force_home and colour != primary and local >= max(0, section_bars - 1):
            if secondary and secondary != primary and not str(secondary).startswith("milonga"):
                return secondary
            extras_list = [p for p in (extras or []) if p and p != primary]
            if "sincopa" in extras_list:
                return "sincopa"
            return colour if colour != "milonga_332" else primary
        return primary

    if role in ("contrast_drive", "contrast_drive_or_ornament"):
        if colour == primary:
            return primary
        run = int(intent.get("contrast_run_bars") or 4)
        if section_bars <= 2:
            return colour
        max_run = max(1, section_bars - 2)
        run = min(max(4, run) if section_bars >= 6 else max(1, run), max_run)
        if run >= 8 and section_bars >= 10:
            run = 8
        elif run >= 4:
            run = 4 if max_run >= 4 else max_run
        run_start = 1
        run_end = run_start + run
        if run_end > section_bars - 1:
            run_end = section_bars - 1
            run_start = max(1, run_end - run)
        if run_start <= local < run_end:
            return colour
        return primary

    return primary


def _legacy_colour_slots(
    primary: str,
    secondary: str | None,
    bar: int,
    *,
    extras: list[str] | None,
    groove: dict[str, Any],
) -> str:
    colour = [
        p for p in ((secondary,) if secondary else ()) + tuple(extras or ())
        if p and p != primary
    ]
    if groove.get("force_primary") or not colour:
        return primary
    slots = tuple(groove.get("colour_slots") or ())
    if not slots:
        slots = (2, 6) if not primary.startswith("milonga") else (6,)
    slot = bar % 8
    if slot not in slots:
        return primary
    return colour[(bar // 8 + slots.index(slot)) % len(colour)]


def apply_microtiming(notes: list[NoteEvent], pulse: PulseParams) -> None:
    if not pulse.bass_on_time or pulse.chord_lag_ms <= 0:
        return
    lag = chord_lag_seconds(pulse)
    for n in notes:
        if n.track == "piano_lh_chord":
            n.start = max(0.0, n.start + lag)


def apply_accent_curve(
    notes: list[NoteEvent],
    *,
    bar_start: float,
    bar_len: float,
    beats_per_bar: int,
    pulse: PulseParams,
    tension: float = 0.5,
) -> None:
    beat_len = bar_len / max(beats_per_bar, 1)
    tension_scale = 0.92 + 0.16 * float(tension)
    for n in notes:
        if n.track not in ("piano_lh", "piano_lh_chord"):
            continue
        rel = n.start - bar_start
        if n.track == "piano_lh_chord" and pulse.chord_lag_ms > 0:
            rel = max(0.0, rel - chord_lag_seconds(pulse))
        beat_idx = int(rel / max(beat_len, 1e-9) + 1e-6)
        mult = accent_multiplier(beat_idx, pulse) * tension_scale
        n.velocity = max(1, min(127, int(n.velocity * mult)))


def apply_staccato_bias(notes: list[NoteEvent], pulse: PulseParams) -> None:
    bias = pulse.staccato_bias
    if bias <= 0.4:
        return
    factor = 1.0 - 0.28 * (bias - 0.4)
    for n in notes:
        if n.track in ("piano_lh", "piano_lh_chord"):
            n.duration = max(0.04, n.duration * factor)


def humanize_with_pulse(n: NoteEvent, rng: Any, pulse: PulseParams) -> None:
    jitter = max(0.005, min(0.035, pulse.humanize_ms / 1000.0))
    n.start = max(0.0, n.start + rng.uniform(-jitter, jitter))
    n.velocity = max(1, min(127, int(n.velocity) + rng.randint(-3, 3)))


def thin_lh_for_drama(
    lh: list[NoteEvent],
    drama_tag: str,
    pulse: PulseParams,
    rng: Any,
) -> tuple[list[NoteEvent], float]:
    silence = pulse.silence_bias
    scale = 1.0
    if drama_tag == "pause":
        keep_one_p = max(0.12, 0.55 - silence * 1.6)
        lh = lh[:1] if lh and rng.random() < keep_one_p else []
        scale = 0.55 * (1.0 - 0.35 * silence)
    elif drama_tag == "anticipate":
        keep_frac = max(0.2, 0.5 - silence * 0.55)
        keep_n = max(1, int(len(lh) * keep_frac)) if lh else 0
        lh = lh[:keep_n]
        scale = 0.7 * (1.0 - 0.25 * silence)
    return lh, scale
