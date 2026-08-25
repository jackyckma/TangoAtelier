# Engine Knowledge Registry

**Last updated:** 2026-08-24  
**Purpose:** Catalog rule-engine knowledge extracted from founder listening feedback, M/E tasks, and research. Each row is addressable for Lab **experiment toggles** and A/B ear tests.

**Related:** `COMPOSE_LAB_SPEC.md`, `MUSICALITY_OVERHAUL.md`, `PROJECT_PLAN.md` §0 filter table.

---

## How to use

| Column | Meaning |
|--------|---------|
| `confidence` | **high** — keep default ON; **medium** — default ON, A/B ok; **experimental** — default OFF or low |
| `flag_key` | Key in `generation_options` (API + skeleton metadata) |
| `layer` | L0–L4 in Compose Lab |

**Principles**

- Bug fixes (M1 spelling, M2 cadence hard rules) are **not** optional.
- Musical hypotheses are **optional** until founder ear confirms.
- Never delete a rule — demote to `flag_key: off` and A/B.

---

## L0 — Shape / narrative

| id | layer | source | confidence | default | flag_key | ear_test |
|----|-------|--------|------------|---------|----------|----------|
| FORM_GOLDEN_AGE | L0 | research §2 | high | on | — | Section labels audible (intro/A/coda) |
| FORM_SEGMENT_24 | L0 | rebrand 2026-08 | high | on | `archetype_id=segment_song` | 24 bars feels like one tema + cadence |
| E9_STRUCTURAL_ANCHORS | L0 | E9 | high | on | — | Climax / A′ entry land in expected bars |
| E10_SETUP_PAYOFF | L0 | E10 | medium | on | — | Coda or late phrase recalls opening cell |
| E11_MOTIVIC_CELLS | L0 | milonga observation | experimental | multi | `motivic_cells` | single=one hook; multi=B contrast |
| DRAMA_ENERGY_CURVE | L0 | E3 | high | on | — | Dense/climax bars louder/denser than intro |

---

## L1 — Harmony

| id | layer | source | confidence | default | flag_key | ear_test |
|----|-------|--------|------------|---------|----------|----------|
| M1_CHORD_SPELLING | L1 | M1 | high | on | — | No wrong V/VII spellings |
| M2_PHRASE_CADENCE | L1 | M2 | high | on | — | Phrases end on V or i/I |
| M2_RELATIVE_MODULATION | L1 | tango convention | high | on | — | B section relative major/minor |
| BRIDGE_V7_PEDAL | L1 | form.py | high | on | — | 4-bar bridge before B |
| PROGRESSION_CHARACTER | L1 | rebrand | high | on | `progression_character` | Each character rolls ≥2 templates; same character ≠ same chords |
| MODE_MAJOR_MINOR | L1 | rebrand | high | on | `mode` | Tonic random; mode matters |
| E5_SURFACE_REHARM | L1 | E5 | experimental | off | `surface_reharm` | V7→V7b9 at high tension only |
| M5_FUNCTIONAL_GRAMMAR | L1 | MUSICALITY | pending | off | `harmonic_grammar` | Not implemented — legacy templates |

---

## L2 — Theme / melody

| id | layer | source | confidence | default | flag_key | ear_test |
|----|-------|--------|------------|---------|----------|----------|
| M4_THREE_PASS | L2 | M4 | high | on | — | Structural → connect → decorate |
| DECLAMATION_UNISON | L2 | founder | high | on | — | Repeated pitch on plateau contour |
| LEAP_RECOVERY | L2 | tango opening | high | on | — | ≥5 semitone leap followed by step back |
| VALS_LYRIC_CAP | L2 | dance rule | high | on | — | Vals ≤3 notes/phrase |
| EXPECTANCY_GATE | L2 | founder 2026-08-20 | high | on | `expectancy_gate` | Stable bars: no mid-sentence chop |
| PHRASE_TRANSFORM | L2 | E11 | experimental | conservative | `phrase_transform_aggressive` | B invert/sequence vs stay on cell |
| YEITES_DECORATE | L2 | M4 pass 3 | medium | medium | `yeites_intensity` | Ornaments only on drive / A′ |
| DENSITY_PARAM | L2 | M4 | high | on | `melody_density` | low/med/high changes notes/bar |
| A_PRIME_ELABORATION | L2 | E2 | high | on | `a_prime_elaboration` | Recap richer than A |

---

## L3 — Groove / LH

| id | layer | source | confidence | default | flag_key | ear_test |
|----|-------|--------|------------|---------|----------|----------|
| M10_PULSE | L3 | M10 | high | on | — | Beat-1 weight; Di Sarli chord lag |
| E12_SECTION_GROOVE | L3 | E12 | high | on | — | Intro sparse, A steady, B drive |
| B_GROOVE_CONTRAST_RUN | L3 | M10 | experimental | on | `b_groove_contrast_run` | B block uses non-home pattern |
| DRAMA_LH_THIN | L3 | founder | high | on | — | Pause/anticipate → sparser LH |
| LH_VOICE_LEADING | L3 | E6 | high | on | — | Bass moves by step when possible |
| BLOCK_BROKEN_MIX | L3 | performance | high | on | — | LH not single ostinato |

---

## L4 — Ensemble / render

| id | layer | source | confidence | default | flag_key | ear_test |
|----|-------|--------|------------|---------|----------|----------|
| SIMPLE_AUDITION_BASE | L4 | Skeleton→Render | high | on | — | Piano-only L2 baseline |
| PERSONALITY_MIX | L4 | render | medium | on | `style_id` | Lead vs accompaniment balance |
| GUITAR_PART | L4 | rebrand v1 | high | on | `ensemble_id` | Solo guitar + comp |
| STRINGS_SPLIT | L4 | render | medium | on | `ensemble_id` | Violin lead / cello pad |
| BANDONEON_PADS | L4 | render | medium | optional | `ensemble_id` | Muted in intro |

---

## Default `generation_options`

```json
{
  "expectancy_gate": true,
  "surface_reharm": "off",
  "motivic_cells": "multi",
  "phrase_transform_aggressive": false,
  "b_groove_contrast_run": true,
  "yeites_intensity": "medium",
  "a_prime_elaboration": true,
  "harmonic_grammar": "legacy_templates"
}
```

---

## A/B workflow (founder)

1. Fix seed + segment (24 bars).
2. Toggle one `flag_key`.
3. Render L2 (simple) or L4 (ensemble).
4. 👍 / 👎 — update `confidence` and default in this file.

---

## Changelog

| Date | Change |
|------|--------|
| 2026-08-24 | Initial registry for Compose Lab rebrand |
