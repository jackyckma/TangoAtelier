# Planner preferences (founder decision patterns)

> Maker REPLAN reads this when framing `decisions.json` recommendations.
> Append durable patterns; keep short. Separate from `AGENTS.md` continual-learning.

## Standing preferences

- Prefer least-dependency, fastest verifiable slice.
- Avoid over-engineering; recommend the lean option.
- API-first, thin UI: contract → API → UI.
- Flag new user-facing features (default off); never flip prod flags autonomously.
- Ask (decisions.json) only for product direction, contracts, milestones, compliance.

## Learned patterns (append-only)

- E11 Motivic cells: **extend** `theme_state` / `_roll_piece_motif` in `skeleton.py`; do not parallel-rewrite the melody engine. Keep `skeleton.motif` backward-compatible (cell 0).
- Decompose engine epics: contract/export → section wiring → development axis → interweave/coda; each slice needs a fixed-seed Python assertion plus `./scripts/agent-verify.sh`.
- Knowledge track (E-03 / K-tasks): **never** invent MuseScore.com or ML-training work to refill the queue. Prefer docs hypotheses → PD metadata ledger → fixture extractor → `knowledge_catalog_v1` default-off. Empty PD allowlist is success when tango-adjacent PD is sparse. Policy file wins over "helpful" corpus ideas.
- M6 development (E-04): **extend** `backend/app/engine/melody/development.py` + wire into existing `skeleton.py` motivic_cells / PitchCell paths. Decompose: pure contract (enum + SECTION_TECHNIQUES + MotifPlan) → parallel export of `motif_development_plans` (T-0016) while phrase technique tags chain (T-0014→T-0015) runs → similarity acceptance. No new user-facing flag; teaching fields export on melody bars only.
- M5 harmony (E-05): **new** `backend/app/engine/harmony/grammar.py` (not a rewrite of `harmony.py` templates). Decompose: FUNCTION_TRANSITIONS + CHORD_CHOICE contract → parallel constraint validators → `generate_functional_progression` + chromatic_bass slice → wire `harmonic_grammar=functional` (default `legacy_templates`) in form/skeleton → entropy/stability acceptance. Colour weight must stay low unless tension/climax gates open. M2 phrase cadence slots are hard rules on top of grammar output.
- **backlog.json must stay valid JSON** — a syntax error makes `loadJson` fall back to empty tasks, which falsely triggers REPLAN and hides ready IMPLEMENT work.
