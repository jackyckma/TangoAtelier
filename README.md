# TangoAtelier

雙語（繁中／英文）阿根廷探戈音樂教學網站：透過**規則引擎**生成原創 MusicXML／MIDI，認識黃金時代不同樂團的節奏與和聲風格，並以視覺化 Hint 輔助鋼琴／吉他即興學習。

> 不播放受版權保護的原曲。網站只以教育目的列出曲名／樂團參考；實際聆聽內容皆為原創生成。

## Status

**Phase 0 in progress：** 前後端骨架與 6 個樂團 Style Profile 已可本機跑。多階段計劃見 [`docs/product/PROJECT_PLAN.md`](docs/product/PROJECT_PLAN.md)。

## Local development

```bash
# API
cd backend && python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
PYTHONPATH=. uvicorn app.main:app --reload --port 8000

# Web (another terminal)
cd frontend && pnpm install && pnpm dev
```

Open http://localhost:5173 — Vite proxies `/api` to the FastAPI server.

## Deploy

Push to `main` → Zeabur GitHub integration（由 founder 設定兩個 service：frontend / backend）。接好後把 Zeabur project ID 與公開 URL 填入 `.agents/instructions/project-guidelines.md` 與 `docs/AGENT_ENV.md`。

## Docs

- [Documentation index](docs/README.md)
- [Current status](docs/CURRENT_STATUS.md)
- [Project plan](docs/product/PROJECT_PLAN.md)
- [Product spec](docs/product/tango-learning-webapp-project-doc.md)

## Agent setup

Bootstrapped from [ai-dev-methodologies](https://github.com/jackyckma/ai-dev-methodologies). See `AGENTS.md` and `.agents/instructions/project-guidelines.md`.
