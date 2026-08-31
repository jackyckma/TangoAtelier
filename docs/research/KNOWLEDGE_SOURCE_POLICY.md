# Knowledge source policy (legally conservative)

**Last updated:** 2026-08-31  
**Status:** Founder-approved default for TangoAtelier  
**Related:** `PROJECT_PLAN.md` §3c (K-tasks), `ENGINE_KNOWLEDGE_REGISTRY.md`, autopilot epic **E-03**

TangoAtelier is likely to remain a **non-commercial / free** teaching tool. There is **no product reason** to take copyright or platform-ToS risk for a larger score corpus. This document is the **source-of-truth allow / deny list** for any agent that mines, scrapes, downloads, or “learns from” musical scores.

This is **not legal advice**. When in doubt: **do not ingest**.

---

## 1. Goal of the knowledge track

Build **abstract tango music-theory knowledge** for the **rule engine** (and Lab A/B flags):

- Phrase / “sentence” shape (length, cadence roles, question–answer)
- Chord-progression **families** (not famous melodies)
- Dance-type rhythm archetypes (tango / milonga / vals)
- Form-level drama (intro / A / B / A′ / coda)

**Output form that may enter the repo or product:**

- Curated hypotheses (JSON / markdown)
- Aggregate statistics (counts, histograms, template IDs)
- Engine rules behind `generation_options` flags (default **off** until ear-approved)

**Must not enter the repo as a redistributable corpus:**

- Full MusicXML / MIDI / PDF of third-party copyrighted works
- Near-complete melody dumps that can reconstruct a known tune
- Bulk downloads from MuseScore.com (any tier)

---

## 2. Allowed sources (prefer in this order)

| Priority | Source | What we may take | Notes |
|----------|--------|------------------|-------|
| **1** | Existing repo research & specs | Abstract rules, listening notes already written | `docs/research/*`, `MUSICALITY_OVERHAUL.md`, Lab specs |
| **2** | Published musicology / textbooks / public pedagogy | Building-block progressions, form conventions, dance pulse descriptions | Cite work; paraphrase into rules — do not copy long score examples into the engine |
| **3** | Founder listening notes (abstract) | “Sounds like X pattern in milonga DJ sets” → hypothesis IDs | No score files required |
| **4** | Confirmed **public domain** or **CC0** scores | Chord-label sequences, phrase/bar lengths, form stats | e.g. filtered **PDMX** rows, IMSLP works with **verified** PD status in the relevant jurisdictions |
| **5** | Tiny hand-built fixtures | Synthetic MusicXML under `backend/tests/fixtures/` | For extractor unit tests only |

**PD / CC0 checklist before any download or commit of score bytes:**

1. Underlying **composition** is PD (or never copyrighted), not only “uploader said so”
2. Arrangement / encoding license is PD, CC0, or otherwise permits our use
3. We store **derived abstract features** in-repo by default; raw PD files stay local/CI cache unless explicitly approved

---

## 3. Forbidden sources / practices

| Forbidden | Why |
|-----------|-----|
| **MuseScore.com** bulk or Pro download → corpus / training / product pipeline | Platform ToS: personal non-commercial download; Licensed Compositions ban ML/AI use; community UGC ≠ PD |
| Treating **community** MuseScore uploads as PD by default | Uploader label can be wrong; Golden Age tango compositions are usually still protected |
| **ML / generative training** on third-party scores (any site) | Out of product scope; high risk; rule engine is the chosen path |
| Scraping / automated download of commercial sheet sites | ToS + copyright |
| Committing copyrighted MusicXML/MIDI/PDF “for later” | Creates redistributable infringement surface |
| Copying a recognizable famous tango **melody** into templates | Product doc already forbids fixed melody libraries of known works |

**Gray zone — do not automate without a new founder decision in `decisions.json`:**

- Manual study of a few copyrighted scores **without** storing them, writing only abstract notes
- Fair-use / 合理使用 claims for a commercial or public product corpus
- Any “we are free so fair use applies” argument as a substitute for this policy

---

## 4. What “sentence” knowledge means here

For K-tasks, a **sentence** (樂句／句子) is an abstract teaching unit, not a copyrighted theme:

- Typical length in bars (e.g. 2+2, 4, 8 for vals)
- Cadence role (half / deceptive / authentic)
- Contour role (question → answer; setup → payoff)
- How it nests inside form (A vs B cell; climax density)

Agents may encode these as **hypotheses** with `confidence` and `evidence` (literature citation or “repo research §…”), then wire them into the engine only behind flags.

---

## 5. Agent rules (non-negotiable)

1. **Do not** add MuseScore.com URLs, API keys, or download scripts for score ingestion.
2. **Do not** add ML training pipelines on score corpora.
3. New knowledge that affects generation ships behind `generation_options` (default **off**) until founder ear sign-off — same Lab discipline as other experimental rules.
4. Prefer **extending** `ENGINE_KNOWLEDGE_REGISTRY.md` + `lab_catalog.py` over parallel engines.
5. If a task would need a forbidden source to meet AC, mark the task `needs_human` and stop — do not stretch the policy.

---

## 6. Tracking

| Artifact | Role |
|----------|------|
| This file | Policy |
| `docs/research/knowledge/` | Hypotheses, allowlists, indexes (created by K-tasks) |
| `docs/product/PROJECT_PLAN.md` §3c | K1–Kn roadmap |
| `docs/autopilot/roadmap.json` **E-03** | Autopilot epic |
| `docs/autopilot/backlog.json` | Machine-checkable tasks |
