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
