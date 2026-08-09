# Project Agent Guidelines — TangoAtelier

Customize this file for **this repository**. Shared methodologies live in `.agents/instructions/` (from [ai-dev-methodologies](https://github.com/jackyckma/ai-dev-methodologies)).

## Communication language

- Respond to the user in **Traditional Chinese（繁體中文）** unless they ask for another language. Cantonese phrasing in user messages is fine to match in tone.
- Keep code, commands, file paths, and quoted source in original language.

## Product

| Item | Value |
|------|-------|
| Name | **TangoAtelier** |
| One-liner | 雙語探戈音樂教學站：規則引擎生成原創 MIDI／MusicXML，配合 Hint 視覺化，學習黃金時代樂團風格與即興 |
| Spec | `docs/product/tango-learning-webapp-project-doc.md` |
| Plan | `docs/product/PROJECT_PLAN.md` |
| Research | `docs/research/milonga_story1.md`, `docs/research/milonga_story2.md` |

## Stack

| Item | Value |
|------|-------|
| Frontend | React (Vite) + TypeScript + `react-i18next` + Tone.js |
| Backend | Python FastAPI + `music21`（規則引擎） |
| Music pipeline | 規則引擎 → music21 Score → **MusicXML**（主產物）＋ `.mid`（下載／相容）＋ note-event JSON（前端播放／Hint） |
| Playback sound | Tone.js + 高品質 soundfont（鋼琴優先，例如 Salamander 類開源 SF）— 不用預設方波／廉價合成器當主力 |
| Package managers | Frontend: `pnpm`；Backend: `uv` 或 `pip` + `requirements.txt`／`pyproject.toml` |
| Test runners | Frontend: Vitest；Backend: pytest |
| Deploy | **Zeabur GitHub integration**（push `main` → auto deploy）。單一 service：repo root `Dockerfile` 建 frontend+API（FastAPI 兼送 SPA）。**不要**維護本機 Docker Compose。 |

## Git branching

| Branch | Purpose |
|--------|---------|
| `main` | Production / Zeabur deploy branch |
| `feat/*` | Feature branches（建議每 Phase 或每大功能一條） |

Workflow: branch from `main` → PR → `main`. Early scaffolding may land directly on `main` when founder asks for initial push.

## Deploy

| Item | Value |
|------|-------|
| Platform | Zeabur（GitHub-linked） |
| GitHub | `jackyckma/TangoAtelier` |
| Zeabur project ID | `6a78ae73e4a69d66638d7bd2` |
| Service ID | `service-6a78b36fe4a69d66638d7d59` |
| Public URL | https://tangoatelier.zeabur.app |
| Deploy branch | `main` |
| Save / Share | Phase 5（不提前做最小版） |

Load Zeabur agent skills when doing deploy/log/env operations. Ask for IDs — do not guess.

## DNS / email (optional)

| Item | Value |
|------|-------|
| DNS provider | Cloudflare（之後有 domain 再填） |
| Domain | *pending* |

## AI providers

| Provider | Env var | Default? |
|----------|---------|----------|
| Minimax | `MINIMAX_API_KEY` | ✅ preferred for **LLM** tasks only |
| OpenAI | `OPENAI_API_KEY` | fallback |
| Anthropic | `ANTHROPIC_API_KEY` | fallback |
| OpenRouter | `OPENROUTER_API_KEY` | experiments |

**Do not** use Minimax Music（或同類 text-to-audio）API 作為音樂生成核心。教學用音樂一律走規則引擎。

## Domain rules (non-negotiable)

1. **無原曲重製** — 只列曲名／樂團／年代作教育參考；播放內容必須是規則生成的原創音樂。
2. **可解釋優先** — 生成邏輯必須能對應 Style Profile（節奏、和聲、配器），以支撐 Hint 教學。
3. **分階段交付** — 每個 Phase 有可驗證產出；驗收通過再進下一 Phase。
4. **視覺** — 簡約、帶淡 Latin／artistic 氛圍；避免過度 fancy（少 glow、重陰影、複雜 collage）。

## Adopted optional practices

- Methodology profile: **Small product** — Tier A + B2 + C；Deploy D1 Zeabur。
- Autopilot (B5) / lane-based (B1)：尚未採用；需要時再啟用。

## Documentation to read before non-trivial work

1. `docs/README.md`
2. `docs/CURRENT_STATUS.md`
3. `docs/SESSION_HANDOFF.md`（resuming）
4. `docs/product/PROJECT_PLAN.md`
5. `docs/product/tango-learning-webapp-project-doc.md`
6. `docs/AGENT_ENV.md`

Update status docs in the same session when behavior or capabilities change materially.

## Spec implementation notes

When implementing a written spec, maintain notes in PR or `docs/product/implementation-notes.md`:

- Design decisions
- Deviations from spec
- Tradeoffs
- Open questions

## Verification before handoff

- Local / Cloud: `./scripts/agent-verify.sh` when present
- After Zeabur is linked: smoke public URL (L4)
