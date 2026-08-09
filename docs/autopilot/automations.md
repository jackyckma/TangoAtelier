# Autopilot automations — thin shells

> Logic lives in **`playbook.md`** (version-controlled). Each Cursor Automation
> only pulls, runs the dispatcher, and executes **one** returned action.
> Edit behavior in the repo — **not** long-term in the Cursor UI.
> Only **triggers** live in the UI.

**Design goal: set these up once and leave them on forever.** Everything you
would otherwise want a UI toggle for — pausing, resuming, starving a project of
work — is a file in the repo instead. See "Control surface" below.

---

## Maker automation

**Trigger (suggested):** `0 */2 * * *` (every 2 hours at :00).  
Slow on purpose — each tick costs tokens even on IDLE.

**Agent Instruction (paste verbatim):**

```
You are the autopilot MAKER (Planner + Worker hats). You produce changes and open PRs; you NEVER merge.

1. git fetch --all -q && git checkout main -q && git pull --rebase -q
2. If scripts/autopilot/decide-next-action.mjs does not exist, STOP NOW: this repo has no autopilot loop. Change nothing, create nothing, report nothing.
3. Run: node scripts/autopilot/decide-next-action.mjs --lane maker
4. If it fails, prints nothing, or returns action IDLE (any reason), STOP. Doing nothing is the correct result. Do not create files, open PRs or issues, invent tasks, scan for work, or repair the loop.
5. Otherwise read docs/autopilot/playbook.md and perform EXACTLY the one action returned (IMPLEMENT / REPLAN), following the "MAKER lane actions" section. Do nothing else. Then stop.
```

## Checker automation

**Trigger (suggested):** `30 */2 * * *` (every 2 hours at :30).

**Agent Instruction (paste verbatim):**

```
You are the autopilot CHECKER (Reviewer + Watchdog + Reporter hats). You verify, merge, guard prod, and report; you NEVER write feature code. You are the ONLY role that merges to main.

1. git fetch --all -q && git checkout main -q && git pull --rebase -q
2. If scripts/autopilot/decide-next-action.mjs does not exist, STOP NOW: this repo has no autopilot loop. Change nothing, create nothing, report nothing.
3. Run: node scripts/autopilot/decide-next-action.mjs --lane checker
4. If it fails, prints nothing, or returns action IDLE (any reason), STOP. Doing nothing is the correct result. Do not create files, open PRs or issues, invent work, or repair the loop.
5. Otherwise read docs/autopilot/playbook.md and perform EXACTLY the one action returned (REVIEW / CLOSE_STALE / WATCHDOG / REPORT), following the "CHECKER lane actions" section. Do nothing else. Then stop.
```

---

## Control surface — stop and start from the repo, not the UI

Once the two Automations exist, you should not need to open the Cursor UI again
to control them. Everything below is a file on `main`, so an agent — or you from
a phone — can change it.

| I want to… | Change on `main` | Effect on next tick |
|---|---|---|
| **Pause everything now** | `docs/autopilot/pause-state.json` → `"paused": true`, set `reason` / `by` | Maker IDLEs; Checker IDLEs (except watchdog recovery it set itself) |
| **Resume** | same file → `"paused": false` | Loop resumes |
| **Let a project idle without pausing** | Leave no `ready` tasks and no `approved` epic with undecomposed scope | Maker IDLEs every tick, silently and cheaply |
| **Stop one task only** | That task's `status` → anything but `ready` | Skipped; rest of queue continues |
| **Wire Automations before the repo is ready** | Do nothing | Dispatcher returns IDLE `no-autopilot-scaffolds`; agent stops without improvising |

**Why this matters:** an Automation that must be manually switched off is a
liability — the moment you need it off is usually the moment you are away from a
computer. A repo file can be changed by anyone you trust, including an agent
acting on your instruction.

**Reserve the UI toggle** for retiring a project permanently, or for a
runaway you cannot reach by git.

## Permissions

- Maker: push to main (for leases / REPLAN docs), create branches, open PRs.
- Checker: push to main, merge PRs, run verify + optional prod smoke.

## Migration from many roles

If you previously had separate Planner / Worker / Reviewer / Watchdog / Reporter
automations: **disable them** and use only Maker + Checker above.
