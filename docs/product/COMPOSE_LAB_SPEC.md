# Compose Lab — Implementation Spec

**Version:** 1.0  
**Date:** 2026-08-24  
**Status:** Implementing  
**Registry:** `ENGINE_KNOWLEDGE_REGISTRY.md`

---

## 1. Product summary

| Item | Value |
|------|-------|
| Name | TangoAtelier (unchanged) |
| Primary URL | `/lab` |
| Legacy redirect | `/atelier` → `/lab` |
| Style Reference | `/orchestras` (copy + deep links) |
| Default segment | **24 bars** (`segment_song` archetype) |
| Target ensemble | Solo piano/guitar → 3–4 parts max |

**One-liner:** Layer-by-layer lab to build a listenable tango segment (solo or small ensemble), lock layers, extend to full arc.

---

## 2. IA & routes

| Route | Component | Notes |
|-------|-----------|-------|
| `/` | HomePage | CTA → `/lab` |
| `/lab` | LabPage | Main compose flow |
| `/atelier` | Redirect | → `/lab` |
| `/orchestras` | OrchestrasPage | Reference; chips +「Compose with this feel」|
| `/orchestras/:id` | OrchestraDetailPage | Link → `/lab?style=&tags=` |

Nav: **Lab** replaces Atelier label; Orchestras → **Style Reference**.

---

## 3. Lab UX flow

```
[Optional tag chips] → Translation panel
  → L0+L1 Build (archetype, mode, progression character, dance)
  → L2 Theme (Simple piano audition) — default focus after build
  → L3 Groove (same skeleton, simple render — groove metadata visible)
  → L4 Ensemble (preset + optional style reference profile)
  → Extend (rebuild golden_age_short, same seed + options)
  → Play + chord grid
```

### Layer lock (v1)

- Client holds `skeleton` after L0 build.
- L2–L4 are **render-only** variants (no skeleton regen unless user clicks Rebuild / Extend).
- `locked_layers: ["shape","harmony","theme"]` stored client-side; Extend clears lock on form only.

---

## 4. API

### `GET /api/lab/options`

Returns:

- `dance_types`, `modes`, `progression_characters`, `archetypes`
- `intent_tags` (bilingual chips + category)
- `ensemble_presets`
- `generation_options_schema` (defaults + labels)
- `style_references` (orchestra cards for L4)

### `POST /api/lab/skeleton`

```json
{
  "dance_type": "tango",
  "mode": "minor",
  "progression_character": "diatonic",
  "archetype_id": "segment_song",
  "melody_density": "medium",
  "melody_variation": "medium",
  "intent_tags": ["lyrical", "sparse"],
  "generation_options": { "expectancy_gate": true },
  "seed": 42
}
```

Response: full skeleton + `generation_options` + `intent_translation` + `segment_bars: 24`.

### `POST /api/lab/render`

```json
{
  "skeleton": { "...": "..." },
  "layer": "theme",
  "ensemble_id": "solo_piano",
  "style_id": "simple",
  "seed": 42,
  "generation_options": {}
}
```

`layer`: `theme` | `groove` | `ensemble`  
- `theme` / `groove`: force `style_id=simple`  
- `ensemble`: uses `ensemble_id` + optional `style_id` for pulse/articulation

### `POST /api/lab/extend`

Same body as skeleton build but `archetype_id: "classic_dance"` and **required** `seed` from prior segment.

Legacy `/api/skeleton`, `/api/render`, `/api/atelier/options` unchanged.

---

## 5. Data models

### Archetypes

| id | form_id | bars (typical) |
|----|---------|-----------------|
| `segment_song` | `segment_song` | 24 |
| `classic_dance` | `golden_age_short` | 60 |

### Form `segment_song`

```
intro(4) + A(16) + cadence(4) = 24
```

### Progression characters

Each character rolls **one** catalog template from a pool (seeded), not a 1:1 map.

| id | minor templates | major templates |
|----|-----------------|-----------------|
| `diatonic` | i-iv-V7-i, i-iv-V7b9-i, borrowed_chords | I-IV-V-I, I-vi-IV-V |
| `descending` | descending_fifths, secondary_dominant | descending_fifths, I-vi-IV-V |
| `chromatic` | chromatic_bass, neapolitan_cadence, secondary_dominant, tritone_substitution_flavour | descending_fifths, I-vi-IV-V |
| `lyrical` | i-VI-III-V7, picardy_close, borrowed_chords | I-vi-IV-V, I-IV-V-I |

### Ensemble presets

| id | piano | guitar | violin/cello | bandoneon |
|----|-------|--------|--------------|-----------|
| `solo_piano` | ✓ | | | |
| `solo_guitar` | | ✓ lead+comp | | |
| `piano_violin` | ✓ | | strings | |
| `small_combo` | ✓ | ✓ | strings | optional |

### Intent tags

File: `backend/data/intent_bundles.json`  
Chip display: bilingual; merge weights into skeleton params + `generation_options`.

---

## 6. Engine changes

| Module | Change |
|--------|--------|
| `catalog.py` | `segment_song` form; progression character map |
| `generation_options.py` | normalize + defaults |
| `intent.py` | load bundles, merge tags → translation |
| `lab_catalog.py` | lab_options() |
| `skeleton.py` | `mode`, `progression_character`, `archetype_id`, `generation_options`, motivic single |
| `render.py` | guitar track; `surface_reharm` from options; ensemble routing |
| `main.py` | lab routes |

---

## 7. Frontend

| File | Change |
|------|--------|
| `LabPage.tsx` | New stepper UI |
| `App.tsx` | `/lab`, redirect `/atelier` |
| `api.ts` | lab fetch/build/render/extend |
| `types.ts` | Lab types |
| `i18n.ts` | lab + reference copy |
| `pianoPlayer.ts` | `guitar` track synth |
| `HomePage`, `Layout`, orchestras pages | CTAs |

---

## 8. Verification

```bash
./scripts/agent-verify.sh
cd backend && PYTHONPATH=. pytest tests/musicality/ -q
```

Manual: backend :8000 + frontend :5173 → `/lab` → tags → build → play 24-bar segment → extend → ensemble.

---

## 9. Out of scope (v1)

- Free-text intent (Phase B)
- Full E8 per-layer skeleton regen API
- M5 functional grammar implementation
- Real guitar/bandoneón samples (synth stand-in)
