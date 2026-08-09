# Agent Instructions (Codex / OpenAI coding agents)

Before non-trivial work, read (in order):

1. `.agents/instructions/karpathy-guidelines.md` — coding discipline
2. `.agents/instructions/judgment-rubrics.md` — done / stuck / escalate / ask
3. `.agents/instructions/project-guidelines.md` — stack, git, deploy, language
4. `.agents/instructions/agent-tooling-guardrails.md` — MCP-first browser; no silent E2E deps

Then consult **`.agents/README.md`** — it maps every other instruction file
to its trigger (decisions, handoff, model dispatch, loops, issues,
methodology sync).

When **resuming**, read `docs/SESSION_HANDOFF.md` first.

Do not duplicate long policy here — keep this file a thin pointer. The
three entry points (`AGENTS.md`, `CLAUDE.md`,
`.cursor/rules/shared-instructions.mdc`) must name the **same** core list;
if you change one, change all three.

## Git workflow

Branch from **`main`**, open PR to **`main`**, unless `project-guidelines.md` states otherwise.

## Cloud Agent sessions

Run `scripts/setup-cloud-agent-env.sh` if present, then `scripts/agent-verify.sh` before handoff.

See `docs/AGENT_ENV.md` for local vs cloud capability matrix.
