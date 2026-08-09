# Session handoff

**Last updated:** 2026-08-09

## Resume here

Phase 0 已部署：https://tangoatelier.zeabur.app （單一 Docker service：FastAPI + SPA）。Save／Share 確認 Phase 5。下一棒：**Phase 1**。

## Context

- Zeabur project `6a78ae73e4a69d66638d7bd2` / service `6a78b36fe4a69d66638d7d59`
- Deploy：repo root `Dockerfile`（不要 Docker Compose）
- 音樂管線：規則引擎 → music21 → MusicXML + MIDI + note-event JSON
- Save／Share：Phase 5
- 溝通：繁體中文

## Verify

```bash
./scripts/agent-verify.sh
curl -sf https://tangoatelier.zeabur.app/health
```

## Blockers

- 無
