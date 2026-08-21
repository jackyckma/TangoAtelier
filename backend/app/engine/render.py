from __future__ import annotations

import random
from typing import Any

from app.engine.export_formats import (
    draft_to_score,
    notes_payload,
    score_to_midi_base64,
    score_to_musicxml,
)
from app.engine.catalog import DANCE_TYPES
from app.engine.groove import (
    apply_accent_curve,
    apply_microtiming,
    apply_staccato_bias,
    humanize_with_pulse,
    pattern_for_groove_bar,
    resolve_pulse,
    thin_lh_for_drama,
)
from app.engine.harmony import chord_pitches
from app.engine.rhythm import choose_rhythm_pair, left_hand_for_bar
from app.engine.types import ChordEvent, NoteEvent, PieceDraft

SIMPLE_PROFILE = {
    "id": "simple",
    "personality_type": "neutral",
    "tempo_bpm_range": [62, 62],
    "rhythm_patterns": ["marcato_en_dos"],
    "articulation": {
        "staccato_level": "medium",
        "rubato_level": "low",
        "dynamic_contrast": "medium",
        "pause_frequency": "low",
    },
    "pulse": {
        "feel": "drive",
        "beat1_weight": 1.05,
        "other_beat_weight": 0.92,
        "bass_on_time": True,
        "chord_lag_ms": 0,
        "humanize_ms": 18,
        "staccato_bias": 0.55,
        "silence_bias": 0.08,
        "colour_aggression": 0.15,
    },
    "instrumentation_defaults": ["piano"],
}

# Melody-forward mixes: RH must read as the song; LH/backdrop support it.
PERSONALITY_MIX = {
    "neutral": {
        "decoration": 0.15,
        "volumes": {
            "piano_lh": 0.62,
            "piano_rh": 1.0,
            "bandoneon": 0.0,
            "strings": 0.0,
            "violin": 0.0,
            "cello": 0.0,
        },
    },
    "rhythmic": {
        "decoration": 0.35,
        "volumes": {
            "piano_lh": 0.78,
            "piano_rh": 1.0,
            "bandoneon": 0.4,
            "strings": 0.2,
            "violin": 0.22,
            "cello": 0.18,
        },
    },
    "lyrical": {
        "decoration": 0.55,
        "volumes": {
            "piano_lh": 0.48,
            "piano_rh": 1.0,
            "bandoneon": 0.55,
            "strings": 0.45,
            "violin": 0.5,
            "cello": 0.38,
        },
    },
    "smooth_powerful": {
        "decoration": 0.3,
        "volumes": {
            "piano_lh": 0.7,
            "piano_rh": 0.98,
            "bandoneon": 0.4,
            "strings": 0.5,
            "violin": 0.48,
            "cello": 0.42,
        },
    },
    "dramatic": {
        "decoration": 0.65,
        "volumes": {
            "piano_lh": 0.72,
            "piano_rh": 1.0,
            "bandoneon": 0.5,
            "strings": 0.55,
            "violin": 0.52,
            "cello": 0.48,
        },
    },
}


def _level_to_01(level: str) -> float:
    return {"low": 0.25, "medium": 0.5, "high": 0.8, "very_high": 1.0}.get(level, 0.5)


def _bpm(profile: dict, rng: random.Random, skeleton: dict) -> float:
    dance_type = skeleton.get("dance_type") or "tango"
    base = float(skeleton.get("default_bpm", DANCE_TYPES.get(dance_type, {}).get("default_bpm", 64)))
    # Dance tempo is authoritative for milonga/vals — orquesta ranges are tango-centric
    if dance_type == "milonga":
        return round(base * rng.uniform(0.96, 1.08), 1)
    if dance_type == "vals":
        return round(base * rng.uniform(0.95, 1.06), 1)
    if profile.get("id") == "simple":
        return base
    lo, hi = profile.get("tempo_bpm_range", [60, 66])
    return float(rng.randint(int(lo), int(hi)))


def _rhythm_pair_for_dance(
    profile: dict, dance_type: str, rng: random.Random
) -> tuple[str, str | None]:
    """Primary groove + optional secondary colour (not whole-piece replace)."""
    dance = DANCE_TYPES.get(dance_type, DANCE_TYPES["tango"])
    if dance_type == "vals":
        return "vals_bass_chord", None
    if dance_type == "milonga":
        primary = str(dance.get("default_rhythm") or "milonga_habanera")
        secondary = str(dance.get("alt_rhythm") or "milonga_332")
        if profile.get("id") == "simple":
            return primary, None
        return primary, secondary
    if profile.get("id") == "simple":
        return str(dance.get("default_rhythm") or "marcato_en_dos"), None
    return choose_rhythm_pair(profile)


def _pattern_for_bar(
    primary: str,
    secondary: str | None,
    bar: int,
    *,
    extras: list[str] | None = None,
    groove: dict[str, Any] | None = None,
    dance_type: str = "tango",
) -> str:
    """M10: groove_role → continuous pattern runs (legacy colour_slots still supported)."""
    return pattern_for_groove_bar(
        primary,
        secondary,
        bar,
        extras=extras,
        groove=groove,
        dance_type=dance_type,
    )


def _lh_power_for_groove(section: str, drama_tag: str, groove: dict[str, Any], elab: dict) -> bool:
    lh = str(groove.get("lh") or "steady")
    if lh in ("busy", "full"):
        return True
    if lh in ("sparse", "cadence"):
        return False
    return drama_tag in ("climax", "rise") or section == "B" or bool(elab)


def _articulation_for_dance(profile: dict, dance_type: str) -> dict:
    base = dict(profile.get("articulation", SIMPLE_PROFILE["articulation"]))
    if dance_type == "milonga":
        # Punchier, less rubato — earthy drive
        base["staccato_level"] = "high" if base.get("staccato_level") != "low" else "medium"
        base["rubato_level"] = "low"
        base["pause_frequency"] = "low"
    elif dance_type == "vals":
        # Flowing — soft 2–3, little chop
        base["staccato_level"] = "low"
        base["rubato_level"] = "medium" if profile.get("id") != "simple" else "low"
        base["pause_frequency"] = "low"
    return base


def _seconds_per_beat(bpm: float) -> float:
    return 60.0 / bpm


def _mix_for(profile: dict) -> dict[str, Any]:
    ptype = profile.get("personality_type", "neutral")
    return PERSONALITY_MIX.get(ptype, PERSONALITY_MIX["neutral"])


def _default_instruments(profile: dict) -> dict[str, bool]:
    defaults = set(profile.get("instrumentation_defaults") or ["piano"])
    return {
        "piano": True,
        "bandoneon": "bandoneon" in defaults and profile.get("id") != "simple",
        "strings": "strings" in defaults and profile.get("id") != "simple",
    }


def _apply_vel(base: int, track_vol: float) -> int:
    return max(1, min(127, int(base * track_vol)))


def _humanize(n: NoteEvent, rng: random.Random, pulse) -> None:
    """M10: deterministic timing/velocity jitter from pulse.humanize_ms."""
    humanize_with_pulse(n, rng, pulse)


def _surface_reharm_symbol(ch: dict, mode: str, tension: float) -> str | None:
    """E5: render-only colour — only when tension clearly asks for it."""
    sym = str(ch.get("symbol") or "")
    if mode == "minor" and sym in ("V", "V7"):
        if (
            tension >= 0.72
            or (
                tension >= 0.62
                and (
                    ch.get("cadence") in ("half", "approach")
                    or str(ch.get("drama") or "") in ("climax", "dense")
                )
            )
        ):
            return "V7b9"
    return None


def _phrase_end_ornament(
    rng: random.Random,
    pitch: int,
    start: float,
    dur: float,
    spb: float,
    vel: int,
    *,
    dance_type: str = "tango",
) -> list[NoteEvent] | None:
    """Replace the cadence attack with an appoggiatura that occupies the same window.

    Returns None when the landing is too short to steal time from.
    """
    if dur < spb * 0.55:
        return None
    if dance_type == "vals":
        steal = min(spb * 0.42, dur * 0.28)
        nb = pitch + rng.choice([-2, -1, 1])
    elif dance_type == "milonga":
        steal = min(spb * 0.22, dur * 0.22)
        nb = pitch + rng.choice([-2, -1])
    else:
        steal = min(spb * 0.2, dur * 0.32)
        nb = pitch + rng.choice([-2, -1, 1])
    if steal < 0.045 or nb == pitch:
        return None
    return [
        NoteEvent(nb, start, steal * 0.92, max(52, vel - 10), "piano_rh"),
        NoteEvent(pitch, start + steal, max(0.06, dur - steal), vel, "piano_rh"),
    ]


def _rh_double_rate(voicing_style: str) -> float:
    """Style-level chance to reinforce lead with octave / chord tone (not skeleton)."""
    return {
        "octave_unison_bass": 0.45,
        "dense_dramatic": 0.55,
        "clear_dance_band": 0.28,
        "singing_legato": 0.22,
        "bright_staccato": 0.18,
    }.get(voicing_style, 0.25)


def _render_melody(
    rng: random.Random,
    melody: list[dict],
    *,
    decoration: float,
    spb: float,
    staccato: str,
    voicing_style: str = "bright_staccato",
    beats_per_bar: int = 2,
    elaborations: dict[int, dict] | None = None,
    dance_type: str = "tango",
    personality: str = "neutral",
) -> list[NoteEvent]:
    """Render RH from skeleton melody; Pass 3 yeites via decorate (M4)."""
    from app.engine.melody.decorate import decorate_melody_events

    adjusted: list[dict] = []
    for m in melody:
        voice = m.get("voice") or "lead"
        if voice == "ornament":
            continue
        mc = dict(m)
        dur_beats = float(mc["duration_beats"])
        drama = mc.get("drama") or "normal"
        if voice != "lead" and staccato == "high":
            dur_beats *= 0.65
        elif staccato == "low" or voice == "lead":
            dur_beats *= 1.08 if voice == "lead" else 1.0
        if drama == "dense":
            dur_beats *= 0.85
        elif drama == "anticipate":
            dur_beats *= 1.15
        elif drama == "rise":
            dur_beats *= 1.05
        mc["duration_beats"] = dur_beats
        adjusted.append(mc)

    notes = decorate_melody_events(
        rng,
        adjusted,
        decoration=decoration,
        spb=spb,
        dance_type=dance_type,
        personality=personality,
        elaborations=elaborations,
        beats_per_bar=beats_per_bar,
    )

    double_rate = _rh_double_rate(voicing_style)
    elab_by_bar = elaborations or {}
    lead_starts = {
        round(float(m["start_beat"]) * spb, 4): m
        for m in adjusted
        if (m.get("voice") or "lead") == "lead"
    }
    extras: list[NoteEvent] = []
    for n in list(notes):
        m = lead_starts.get(round(n.start, 4))
        if m is None or n.duration < spb * 0.45:
            continue
        bar = int(float(m["start_beat"]) // max(beats_per_bar, 1))
        elab = elab_by_bar.get(bar) or {}
        orn_boost = float(elab.get("ornament_boost") or 0)
        p_double = double_rate
        if orn_boost:
            p_double = min(0.7, p_double + orn_boost * 0.35)
        drama = m.get("drama") or "normal"
        phrase_end = bool(m.get("phrase_end"))
        if drama == "climax" and phrase_end:
            p_double = min(0.75, p_double + 0.2)
        elif phrase_end:
            p_double = min(0.55, p_double + 0.1)
        else:
            p_double *= 0.45
        if rng.random() < p_double:
            below = n.pitch - 12
            if below >= 48:
                extras.append(
                    NoteEvent(
                        below,
                        n.start,
                        max(0.05, n.duration * 0.92),
                        max(48, n.velocity - 22),
                        "piano_rh",
                    )
                )
    notes.extend(extras)
    notes.sort(key=lambda x: (x.start, x.pitch))
    return notes


def _chord_tonality(ch: dict, skeleton: dict) -> tuple[int, str]:
    return int(ch.get("tonic", skeleton["tonic"])), str(ch.get("mode", skeleton["mode"]))


def _bandoneon_pads(
    skeleton: dict,
    *,
    spb: float,
    lyrical: bool,
) -> list[NoteEvent]:
    """Long mid-register chord holds — harmonic backdrop, not melody doubling."""
    notes: list[NoteEvent] = []
    beats_per_bar = int(skeleton["beats_per_bar"])
    bar_len = beats_per_bar * spb
    chords = skeleton["chords"]
    i = 0
    while i < len(chords):
        ch = chords[i]
        symbol = ch["symbol"]
        tonic, mode = _chord_tonality(ch, skeleton)
        hold_bars = 1
        while (
            i + hold_bars < len(chords)
            and chords[i + hold_bars]["symbol"] == symbol
            and chords[i + hold_bars].get("key", ch.get("key")) == ch.get("key")
            and hold_bars < 2
        ):
            hold_bars += 1
        pitches = chord_pitches(tonic, mode, symbol, octave_shift=0)
        mid = [p + 12 for p in pitches[: (3 if lyrical else 2)]]
        start = int(ch["bar"]) * bar_len
        dur = hold_bars * bar_len * (0.95 if lyrical else 0.88)
        for p in mid:
            notes.append(
                NoteEvent(p, start, dur, 62 if lyrical else 54, "bandoneon")
            )
        i += hold_bars
    return notes


def _strings_section(
    skeleton: dict,
    *,
    spb: float,
    dramatic: bool,
    lyrical: bool,
) -> list[NoteEvent]:
    """Split string section: violin (high) + cello (low), phrase-length sustains."""
    notes: list[NoteEvent] = []
    beats_per_bar = int(skeleton["beats_per_bar"])
    bar_len = beats_per_bar * spb
    chords = skeleton["chords"]
    i = 0
    while i < len(chords):
        ch = chords[i]
        section = str(ch.get("section") or "A")
        if section == "intro":
            i += 1
            continue
        tonic, mode = _chord_tonality(ch, skeleton)
        symbol = ch["symbol"]
        hold = 1
        max_hold = 4 if lyrical else (3 if dramatic else 2)
        while (
            i + hold < len(chords)
            and chords[i + hold]["symbol"] == symbol
            and chords[i + hold].get("key", ch.get("key")) == ch.get("key")
            and str(chords[i + hold].get("section") or "") == section
            and hold < max_hold
        ):
            hold += 1

        pitches = chord_pitches(tonic, mode, symbol, octave_shift=0)
        root = pitches[0]
        third = pitches[1] if len(pitches) > 1 else root + 3
        fifth = pitches[2] if len(pitches) > 2 else root + 7
        start = int(ch["bar"]) * bar_len
        dur = hold * bar_len * (0.96 if lyrical else 0.9)

        # Violin: mid-high chord tones
        violin_tones = [third + 12, fifth + 12] if lyrical else [fifth + 12, third + 12]
        if dramatic and hold >= 2:
            violin_tones = [third + 12, fifth + 12, root + 24]
        for p in violin_tones[: 3 if dramatic else 2]:
            notes.append(NoteEvent(p, start, dur, 48 if not dramatic else 56, "violin"))

        # Cello: low root / fifth
        cello_tones = [root - 12, fifth - 12] if root >= 48 else [root, fifth]
        if section in ("A", "A_prime") and not dramatic:
            cello_tones = [root - 12]
        for p in cello_tones:
            notes.append(
                NoteEvent(max(28, p), start, dur * 1.02, 44 if not dramatic else 50, "cello")
            )
        i += hold
    return notes


def render_skeleton(
    skeleton: dict[str, Any],
    profile: dict,
    *,
    seed: int | None = None,
    instruments: dict[str, bool] | None = None,
    include_midi: bool = True,
    include_musicxml: bool = False,
) -> dict[str, Any]:
    seed = int(seed if seed is not None else skeleton.get("seed") or random.randint(1, 2_147_483_647))
    style_salt = sum(ord(c) for c in str(profile.get("id", "x")))
    rng = random.Random(seed ^ style_salt)

    bpm = _bpm(profile, rng, skeleton)
    spb = _seconds_per_beat(bpm)
    beats_per_bar = int(skeleton["beats_per_bar"])
    bar_len = beats_per_bar * spb
    time_signature = tuple(skeleton["time_signature"])
    dance_type = str(skeleton.get("dance_type") or "tango")
    pulse = resolve_pulse(profile)
    rhythm_primary, rhythm_secondary = _rhythm_pair_for_dance(profile, dance_type, rng)
    rhythm_extras = [
        p
        for p in (profile.get("rhythm_patterns") or [])
        if p not in (rhythm_primary, rhythm_secondary)
    ]
    # Single-pattern styles (e.g. D'Arienzo) still need occasional colour
    if dance_type == "tango" and not rhythm_secondary and not rhythm_extras and profile.get("id") != "simple":
        rhythm_extras = ["sincopa"] if rhythm_primary.startswith("marcato") else ["marcato_en_dos"]
    articulation = _articulation_for_dance(profile, dance_type)
    tonic = int(skeleton["tonic"])
    mode = skeleton["mode"]
    mix = _mix_for(profile)
    vols = dict(mix["volumes"])
    decoration = float(mix["decoration"])
    decoration = min(
        1.0,
        decoration * 0.75
        + 0.25 * _level_to_01(str(articulation.get("dynamic_contrast", "medium"))),
    )
    if profile.get("id") == "simple":
        decoration = 0.12
    if dance_type == "milonga":
        decoration *= 0.4
    elif dance_type == "vals":
        decoration *= 0.35

    enabled = _default_instruments(profile)
    if instruments:
        for k in ("piano", "bandoneon", "strings"):
            if k in instruments:
                enabled[k] = bool(instruments[k])

    for layer, floor in (("bandoneon", 0.5), ("violin", 0.4), ("cello", 0.35)):
        if layer == "bandoneon":
            if enabled.get("bandoneon") and vols.get("bandoneon", 0) < 0.15:
                vols["bandoneon"] = floor
        elif enabled.get("strings") and vols.get(layer, 0) < 0.15:
            vols[layer] = floor
    if enabled.get("strings") and vols.get("strings", 0) < 0.15:
        vols["strings"] = 0.45

    notes: list[NoteEvent] = []
    chord_events: list[ChordEvent] = []

    for ch in skeleton["chords"]:
        bar = int(ch["bar"])
        ch_tonic, ch_mode = _chord_tonality(ch, skeleton)
        chord_events.append(
            ChordEvent(
                bar=bar,
                symbol=str(ch["symbol"]),
                start=bar * bar_len,
                duration=bar_len,
                mode=ch_mode,
                tonic=ch_tonic,
                key_name=str(ch.get("key") or skeleton.get("key") or ""),
            )
        )

    voicing = str(
        (profile.get("harmonic_tendencies") or {}).get("voicing_style") or "bright_staccato"
    )

    if enabled.get("piano", True):
        elaborations: dict[int, dict] = {}
        for ch in skeleton["chords"]:
            el = ch.get("elaboration")
            if isinstance(el, dict):
                elaborations[int(ch["bar"])] = el
        tension_curve = list(skeleton.get("tension_curve") or [])
        prev_bass: int | None = None
        pattern_by_bar: dict[int, str] = {}

        for ch in skeleton["chords"]:
            bar = int(ch["bar"])
            section = str(ch.get("section") or "A")
            drama_tag = str(ch.get("drama") or "normal")
            energy = float(ch.get("energy") or 0.5)
            tension = float(tension_curve[bar]) if bar < len(tension_curve) else energy
            elab = elaborations.get(bar) or {}
            ch_tonic, ch_mode = _chord_tonality(ch, skeleton)
            surface = _surface_reharm_symbol(ch, ch_mode, tension)
            pitches = chord_pitches(ch_tonic, ch_mode, surface or ch["symbol"])
            bar_start = bar * bar_len
            # E12: section groove intent — same base family, different depth by form
            groove = ch.get("groove") if isinstance(ch.get("groove"), dict) else (
                (skeleton.get("section_groove") or {}).get(section) or {}
            )
            pattern = _pattern_for_bar(
                rhythm_primary,
                rhythm_secondary,
                bar,
                extras=rhythm_extras,
                groove=groove,
                dance_type=dance_type,
            )
            pattern_by_bar[bar] = pattern
            lh_kind = str(groove.get("lh") or "steady")
            lh = left_hand_for_bar(
                pattern,
                bar,
                bar_start,
                bar_len,
                pitches,
                articulation,
                beats_per_bar=beats_per_bar,
                voicing_style=voicing,
                power=_lh_power_for_groove(section, drama_tag, groove, elab),
                lh_upgrade=str(elab["lh_upgrade"]) if elab.get("lh_upgrade") else (
                    "busier" if lh_kind == "full" and section == "A_prime" and not elab else None
                ),
                prev_bass=prev_bass,
            )
            if lh:
                prev_bass = min(n.pitch for n in lh)
            lh_scale = vols.get("piano_lh", 0.8)
            # E3: tension lifts accompaniment weight into the peak
            lh_scale *= 0.88 + 0.28 * tension
            if lh_kind == "sparse" or section in ("intro", "bridge"):
                lh_scale *= 0.78
                lh = lh[: max(1, (len(lh) + 1) // 2)] if lh and lh_kind == "sparse" else lh
            elif lh_kind == "cadence" or section == "coda":
                lh_scale *= 0.8
                lh = lh[: max(1, len(lh) // 2 + 1)] if lh else lh
            elif section == "A" and lh_kind == "steady":
                lh_scale *= 0.82  # make room for the theme
            elif lh_kind == "busy":
                lh_scale *= 0.95
            elif section == "A_prime" or lh_kind == "full":
                # Recap: fuller LH (elaboration) while still leaving the lead audible
                lh_scale *= 0.92 + 0.15 * float(elab.get("dynamics_boost") or 0)
            if drama_tag in ("pause", "anticipate"):
                lh, drama_scale = thin_lh_for_drama(lh, drama_tag, pulse, rng)
                lh_scale *= drama_scale
            elif drama_tag == "rise":
                lh_scale *= 0.95 + 0.15 * energy
            elif drama_tag == "climax":
                lh_scale *= 1.12
            elif drama_tag == "release":
                lh_scale *= 0.9
            elif drama_tag == "dense":
                lh_scale *= 1.05
            else:
                lh_scale *= 0.85 + 0.3 * energy

            # Weak-beat thinning before accent so beat-1 weight isn't inverted by drops
            kept: list = []
            for n in lh:
                if section in ("A", "A_prime", "B") and beats_per_bar == 2:
                    rel = (n.start - bar_start) / max(bar_len, 1e-6)
                    if (
                        section != "A_prime"
                        and 0.4 < rel < 0.6
                        and n.velocity < 90
                        and drama_tag not in ("climax", "rise")
                    ):
                        continue
                kept.append(n)
            lh = kept

            apply_accent_curve(
                lh,
                bar_start=bar_start,
                bar_len=bar_len,
                beats_per_bar=beats_per_bar,
                pulse=pulse,
                tension=tension,
            )
            apply_staccato_bias(lh, pulse)
            apply_microtiming(lh, pulse)

            for n in lh:
                n.velocity = _apply_vel(n.velocity, lh_scale)
                notes.append(n)

        rh = _render_melody(
            rng,
            skeleton["melody"],
            decoration=decoration,
            spb=spb,
            staccato=str(articulation.get("staccato_level", "medium")),
            voicing_style=voicing,
            beats_per_bar=beats_per_bar,
            elaborations=elaborations,
            dance_type=dance_type,
            personality=str(profile.get("personality_type") or "neutral"),
        )
        for n in rh:
            n.velocity = _apply_vel(n.velocity, vols.get("piano_rh", 1.0))
            notes.append(n)
    else:
        pattern_by_bar = {}

    if enabled.get("bandoneon"):
        bn = _bandoneon_pads(
            skeleton,
            spb=spb,
            lyrical=profile.get("personality_type") == "lyrical",
        )
        for n in bn:
            # Mute pads during intro — leave air for the theme entrance
            bar_idx = int(n.start / max(bar_len, 1e-6))
            sec = "A"
            if bar_idx < len(skeleton["chords"]):
                sec = str(skeleton["chords"][bar_idx].get("section") or "A")
            if sec == "intro":
                continue
            scale = vols.get("bandoneon", 0.7) * (
                0.65 if sec == "A" else (0.88 if sec == "A_prime" else 1.0)
            )
            n.velocity = _apply_vel(n.velocity, scale)
            notes.append(n)

    if enabled.get("strings"):
        st = _strings_section(
            skeleton,
            spb=spb,
            dramatic=profile.get("personality_type") == "dramatic",
            lyrical=profile.get("personality_type") == "lyrical",
        )
        for n in st:
            bar_idx = int(n.start / max(bar_len, 1e-6))
            sec = "A"
            if bar_idx < len(skeleton["chords"]):
                sec = str(skeleton["chords"][bar_idx].get("section") or "A")
            theme_scale = 0.7 if sec == "A" else (0.95 if sec == "A_prime" else 1.0)
            if n.track == "violin":
                base = vols.get("violin", vols.get("strings", 0.45))
            else:
                base = vols.get("cello", vols.get("strings", 0.4) * 0.85)
            n.velocity = _apply_vel(n.velocity, base * theme_scale)
            notes.append(n)

    notes.sort(key=lambda n: (n.start, n.track, n.pitch))
    for n in notes:
        if n.track in ("piano_lh", "piano_lh_chord", "piano_rh"):
            _humanize(n, rng, pulse)
    notes.sort(key=lambda n: (n.start, n.track, n.pitch))
    rhythm_label = rhythm_primary
    if rhythm_secondary:
        rhythm_label = f"{rhythm_primary}+{rhythm_secondary}"
    draft = PieceDraft(
        orchestra_id=profile["id"],
        seed=seed,
        bpm=bpm,
        key_name=skeleton["key"],
        mode=mode,
        time_signature=time_signature,  # type: ignore[arg-type]
        rhythm_pattern=rhythm_label,
        form=list(skeleton.get("form") or []),
        notes=notes,
        chords=chord_events,
        bars=int(skeleton["bars"]),
    )
    score = draft_to_score(draft)
    duration = draft.bars * bar_len
    payload: dict[str, Any] = {
        "orchestra_id": draft.orchestra_id,
        "skeleton_seed": skeleton.get("seed"),
        "seed": draft.seed,
        "bpm": draft.bpm,
        "key": draft.key_name,
        "mode": draft.mode,
        "dance_type": dance_type,
        "time_signature": list(draft.time_signature),
        "rhythm_pattern": draft.rhythm_pattern,
        "form": draft.form,
        "progression_id": skeleton.get("progression_id"),
        "melody_density": skeleton.get("melody_density"),
        "melody_variation": skeleton.get("melody_variation"),
        "decoration": round(decoration, 3),
        "volumes": vols,
        "instruments": enabled,
        "bars": draft.bars,
        "duration_seconds": round(duration, 2),
        # M10: pulse snapshot + per-bar LH pattern
        # Track choice: bass/root = piano_lh (on time); lagged blocks = piano_lh_chord
        "pulse": {
            "feel": pulse.feel,
            "beat1_weight": pulse.beat1_weight,
            "other_beat_weight": pulse.other_beat_weight,
            "chord_lag_ms": pulse.chord_lag_ms,
            "humanize_ms": pulse.humanize_ms,
            "silence_bias": pulse.silence_bias,
        },
        "lh_pattern_by_bar": {str(k): v for k, v in sorted(pattern_by_bar.items())},
        "chords": [
            {
                "bar": c.bar,
                "symbol": c.symbol,
                "start": round(c.start, 4),
                "duration": round(c.duration, 4),
                "key": skeleton["chords"][i].get("key"),
                "mode": skeleton["chords"][i].get("mode"),
                "section": skeleton["chords"][i].get("section"),
                "cadence": skeleton["chords"][i].get("cadence"),
                "elaboration": skeleton["chords"][i].get("elaboration"),
            }
            for i, c in enumerate(draft.chords)
        ],
        "harmony_plan": skeleton.get("harmony_plan"),
        "drama": skeleton.get("drama"),
        "motivic_cells": skeleton.get("motivic_cells"),
        "motivic_section_map": skeleton.get("motivic_section_map"),
        "tension_curve": skeleton.get("tension_curve"),
        "notes": notes_payload(draft.notes),
    }
    if include_midi:
        payload["midi_base64"] = score_to_midi_base64(score)
    if include_musicxml:
        payload["musicxml"] = score_to_musicxml(score)
    return payload
