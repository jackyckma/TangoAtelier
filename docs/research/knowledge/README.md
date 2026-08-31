# Knowledge track — hypotheses & indexes

**Status:** K1 scaffold (autopilot **T-0007**)  
**Policy:** [KNOWLEDGE_SOURCE_POLICY.md](../KNOWLEDGE_SOURCE_POLICY.md)  
**Roadmap:** [PROJECT_PLAN.md](../../product/PROJECT_PLAN.md) §3c (K-tasks)

This directory holds **abstract tango music-theory knowledge** for the rule engine and Lab flags. It is the in-repo home for curated hypotheses, allowlists, and aggregate statistics — not for score corpora.

---

## Allowed outputs (may live here)

| Artifact | Purpose |
|----------|---------|
| `hypotheses/*.json` | One hypothesis per file; must validate against `hypothesis.schema.json` |
| `pd_allowlist.json` | PD/CC0 metadata ledger (K3); entries only — no score bytes |
| `fixture_stats.example.json` | Optional abstract stats shape from fixture extractors (K4) |
| This README | Index, policy links, agent constraints |

Hypotheses encode teaching units (sentence shape, progression families, rhythm archetypes, form drama) with `confidence`, `evidence`, and optional `engine_hint` for future flag-gated wiring.

---

## Explicitly forbidden

Per [KNOWLEDGE_SOURCE_POLICY.md](../KNOWLEDGE_SOURCE_POLICY.md):

- **MuseScore.com** ingestion — no bulk download, API keys, or scrape scripts for score corpora
- Full MusicXML / MIDI / PDF of third-party copyrighted works
- Near-complete melody dumps that could reconstruct known tunes
- ML / generative training pipelines on third-party scores

Agents that need a forbidden source to meet acceptance must mark the task `needs_human` and stop — do not stretch the policy.

---

## Layout

```
knowledge/
├── README.md                 ← this file
├── hypothesis.schema.json    ← JSON Schema for one hypothesis object
├── hypotheses/               ← curated JSON (K2+)
├── pd_allowlist.json         ← PD/CC0 ledger (K3)
└── (optional stats examples)
```

---

## Hypothesis schema

See `hypothesis.schema.json` (JSON Schema draft-07). Required fields: `id`, `title`, `layer`, `kind`, `confidence`, `evidence`, `summary`, `engine_hint`.

Example filename: `hypotheses/TANGO_SENT_QA_4BAR.json` where the stem equals `id`.

---

## Related docs

- [KNOWLEDGE_SOURCE_POLICY.md](../KNOWLEDGE_SOURCE_POLICY.md) — allow / deny list
- [ENGINE_KNOWLEDGE_REGISTRY.md](../ENGINE_KNOWLEDGE_REGISTRY.md) — engine-facing registry
- [PROJECT_PLAN.md](../../product/PROJECT_PLAN.md) §3c — K1–K5 roadmap
- Autopilot epic **E-03** in `docs/autopilot/roadmap.json`
