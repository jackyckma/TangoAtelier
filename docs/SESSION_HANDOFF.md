# Session handoff

**Last updated:** 2026-08-09

## Resume here

Phase 1 已 push／部署中。驗收：開 https://tangoatelier.zeabur.app → 樂團詳情 → 生成 → 播放（首次需載入 Salamander samples）。下一 Phase 依計劃為 Phase 2（完整曲式）或 Phase 4（Hint）——與 founder 確認優先序。

## Context

- Zeabur：project `6a78ae73e4a69d66638d7bd2` / service `6a78b36fe4a69d66638d7d59`
- 引擎：`backend/app/engine/`（rhythm / harmony / melody / generator）
- 播放：`frontend/src/audio/pianoPlayer.ts`（Tone.Sampler + Salamander CDN）
- Save／Share：Phase 5

## Verify

```bash
./scripts/agent-verify.sh
curl -sf -X POST https://tangoatelier.zeabur.app/api/generate \
  -H 'content-type: application/json' \
  -d '{"orchestra_id":"d_arienzo","seed":1}' | head -c 200
```
