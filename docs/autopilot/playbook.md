# Autopilot playbook — the file the automations execute

> **This file IS the automation logic.** Each Cursor Automation is a thin shell:
> pull → run dispatcher → do exactly one action below → stop.
>
> - **Maker** — produces changes; **never merges.**
> - **Checker** — verifies, merges, optional prod guard, reports; **never writes feature code.**

## Every run

```bash
git fetch --all -q && git checkout main -q && git pull --rebase -q
node scripts/autopilot/decide-next-action.mjs --lane <maker|checker>
```

Execute only the returned JSON `action`. If `IDLE`, stop — see §0.

Prefer dependency-free verify commands documented in `docs/AGENT_ENV.md`.

---

## §0 Stop conditions — read before anything else

Automations are meant to stay **switched on permanently**. That only works if
"there is nothing to do" is a cheap, silent, zero-trace outcome. Doing nothing
well is a first-class result, not a failure.

**`IDLE` means: stop immediately and leave no trace.** Specifically, do **not**:

- open a PR, branch, issue, or commit — including to `docs/`
- "helpfully" invent work, scan the codebase for problems, or propose tasks
- write a status comment, log file, or note anywhere
- explain at length why you are idle — one line of output is enough

An idle tick should cost roughly one command. If you find yourself reasoning
about what *could* be done, you have already exceeded your mandate: the queue is
the mandate.

**Stop, changing nothing, in every one of these cases:**

| Condition | What it means | Do |
|---|---|---|
| `action: IDLE` | No actionable work this tick | Stop |
| `reason: no-autopilot-scaffolds` | Repo has no `docs/autopilot/` — never fueled | Stop. **Do not create scaffolds.** Fueling a repo is a founder decision |
| Dispatcher missing / throws / prints nothing | Loop is not installed here, or is broken | Stop. Do not proceed from memory, and do not repair the loop as a side quest |
| `pause-state.json` → `paused: true` | Kill-switch is on | Stop (Checker: only `WATCHDOG` recovery, and only when `by: deploy-watchdog`) |
| Output is not one of the actions below | Unknown state | Stop. Unknown ≠ improvise |

**Pausing and resuming is done in the repo, not in the Cursor UI.** Set
`docs/autopilot/pause-state.json` → `"paused": true` on `main` and both lanes
hold on the next tick; set it back to `false` to resume. This is deliberate: the
switch lives where an agent or a phone can reach it, so nobody has to be at a
desk to stop a loop. Toggling the Automation itself in the UI should be reserved
for retiring a project for good.

---

## MAKER lane actions

### `IMPLEMENT` (payload: `taskId`, `task`)

**Lock on `main` first — never only on the feature branch.**

1. `git checkout main && git pull --rebase`.
2. Lease on **main**:
   - `backlog.json`: task `status: in_progress`.
   - `locks.json`: `"locks": { "<taskId>": { "by": "maker", "since": "<ISO>", "branch": null, "pr": null } }`.
   - Commit + **push to `main`**. Only then create a feature branch.
3. `git checkout -b cursor/…` from that tip. Implement per task `description`.
   New user-facing behavior **must** use the task's `flag` (default off).
   Stage only changed files — **never `git add -A`**. Prefer not editing
   backlog/locks on the feature branch.
4. Run every `acceptance` command (+ project base verify). All must exit 0.
   - Green → `gh pr create` with title including **`T-xxxx`**. Draft OK.
     On **main**: `status: in_review`, set lock `pr` + `branch`, append
     `feedback`, push **main**. **Do NOT merge.**
   - Mechanical fail & retries left → on main: clear lock, `ready`,
     increment `retries`, log error, push.
   - Judgment fail / retries exhausted → on main: clear lock,
     `needs_human`, push. Never replan judgment tasks yourself.

### `REPLAN`

Edit **only** `docs/autopilot/*`. No app code / flags / PR merges.

1. `node scripts/autopilot/apply-decision-defaults.mjs` — flip `unblocks` tasks to `ready` when auto-decided.
2. `node scripts/autopilot/queue-status.mjs`.
3. Decompose the next `approved` epic into small `ready` tasks
   (contract → API → thin UI), each with machine-checkable `acceptance`.
   - Reversible → ready tasks (decide-and-log).
   - Direction / contract / compliance → `decisions.json` (options + recommendation;
     `default_if_silent` null only for high-stakes).
   - Never invent direction → `proposed` epic + decision.
4. Optionally append durable patterns to `planner-preferences.md`.
5. Commit + push `docs/autopilot/*` to main (no PR).

**If no epic is `approved`, REPLAN is not offered — you will get `IDLE`.** An
empty roadmap means the founder has not chosen a direction yet; proposing one is
not your job.

### `IDLE`

Stop. See §0.

---

## CHECKER lane actions

> Exclude branches containing `learner` from auto-merge (founder-gated process PRs).

### `CLOSE_STALE` (`pr`, `branch`, `taskId?`)

If task is `done` on main or `locks.json` points at another PR for the same
`T-xxxx`: close this PR as superseded. Do not change backlog for the winner.

### `REVIEW` (`pr`, `branch`)

You did not author this PR.

1. Superseded? → `CLOSE_STALE`.
2. Checkout PR head; `node scripts/autopilot/verify-all.mjs`. FAIL → comment,
   bounce task to `ready` or `needs_human`, never merge.
3. Scope: diff matches task description; new UX behind flag.
4. Sensitive paths (auth/API/DB) → security review if available; block on high-confidence findings.
5. Green → `gh pr ready` then `gh pr merge --merge --delete-branch`.
   On main: task `done`, clear lock, push. Close duplicate `T-xxxx` PRs.

### `WATCHDOG`

1. Allow deploy time after merge if the project auto-deploys.
2. `node scripts/autopilot/deploy-watchdog.mjs`.
   - PASS → stop.
   - FAIL → pause set (`by=deploy-watchdog`). Revert the bad merge if safe,
     note `needs_human`, re-run watchdog after recovery.

If no `prod_smoke_cmd` is configured, watchdog only records the main sha (see
`project-hooks.json`).

### `REPORT` (`kind` = daily | weekly)

- daily: `node scripts/autopilot/render-report.mjs > docs/autopilot/reports/$(date -u +%F).md`
- weekly: `node scripts/autopilot/weekly-report.mjs > docs/autopilot/reports/weekly-$(date -u +%F).md`
- Commit + push reports. No feature code.

If the project has opted in to hub reporting (`orbita_hub: true` in
`project-hooks.json`), also regenerate the machine-readable report per
`.agents/instructions/portfolio-hub-reporting.md`.

### `IDLE`

Stop. See §0.
