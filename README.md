# TangoAtelier

雙語（繁中／英文）阿根廷探戈音樂教學網站：透過**規則引擎**生成原創 MusicXML／MIDI，認識黃金時代不同樂團的節奏與和聲風格，並以視覺化 Hint 輔助鋼琴／吉他即興學習。

> 不播放受版權保護的原曲。網站只以教育目的列出曲名／樂團參考；實際聆聽內容皆為原創生成。

## Status

Scaffolding 完成。多階段計劃見 [`docs/product/PROJECT_PLAN.md`](docs/product/PROJECT_PLAN.md)。

## Stack (planned)

| Layer | Choice |
|-------|--------|
| Frontend | React (Vite) + TypeScript + Tone.js |
| Backend | FastAPI + music21 |
| Deploy | GitHub `main` → Zeabur |

## Docs

- [Documentation index](docs/README.md)
- [Current status](docs/CURRENT_STATUS.md)
- [Project plan](docs/product/PROJECT_PLAN.md)
- [Product spec](docs/product/tango-learning-webapp-project-doc.md)

## Agent setup

Bootstrapped from [ai-dev-methodologies](https://github.com/jackyckma/ai-dev-methodologies). See `AGENTS.md` and `.agents/instructions/project-guidelines.md`.
