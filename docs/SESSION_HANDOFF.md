# Session handoff

**Last updated:** 2026-08-09

## Resume here

Phase 0 程式已在 `main`（或即將 push）。本機驗收：起 backend:8000 + frontend:5173，確認列表／詳情／i18n。接著 Phase 1 規則引擎＋Tone.js soundfont。

## Context

- Deploy：Zeabur only；無 Docker Compose
- 音樂管線：規則引擎 → music21 → MusicXML + MIDI + note-event JSON
- Save／Share：Phase 5；可討論 Phase 1 後最小版
- 溝通：繁體中文

## Verify

```bash
./scripts/agent-verify.sh
```

## Blockers

- Zeabur IDs／URL：等 founder（不擋本機 Phase 1）
