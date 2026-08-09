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

## Learned User Preferences

- Visual direction: simple / minimal with a light artistic and Latin feel; avoid overly fancy UI.
- Production deploy is Zeabur via GitHub `main` integration; do not maintain Docker Compose for deploy.
- After a coherent change set on this project, commit and push to `main` without waiting to ask (unless risky, secrets-related, or the founder says to hold).
- Prefer a rule-engine music path (not AI music APIs as the core); playback should sound musical, not like a cheap synth.
- Preferred compose UX: generate a dance-type skeleton first (Tango / Milonga / Waltz plus shared params such as key, progression, form), then let users compare orchestra-style renderings of the same piece.
- Keep generation/playback on the orchestra detail view so users can read the orchestra description while listening.
- Orchestra style rendering should aim beyond crude rhythm caricatures (decoration, relative instrument balance, optional backdrop instruments) so Golden Age styles are not oversimplified for aficionados.

## Learned Workspace Facts

- Product name is TangoAtelier: a bilingual Argentine tango teaching site focused on improvisation and style listening via generated MusicXML / MIDI / note events.
- GitHub repo is `jackyckma/TangoAtelier`; production URL is `https://tangoatelier.zeabur.app` (single Zeabur service: root Dockerfile, FastAPI serves API + SPA).
- Zeabur project ID `6a78ae73e4a69d66638d7bd2`; service ID `service-6a78b36fe4a69d66638d7d59`.
- Phase 0 ships six orchestras as a starter set covering four personalities, not a hard roster cap; more orchestras from research docs can be added later as Style Profiles.
- Save / rename / share of generated pieces is planned for Phase 5, not earlier phases by default.
- Generation pipeline center of gravity: music21 Score → MusicXML (primary), MIDI, and note-event JSON for Tone.js + teaching hints.
