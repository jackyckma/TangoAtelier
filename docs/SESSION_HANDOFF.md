# Session handoff

**Last updated:** 2026-08-09

## Resume here

Atelier 雙層流程已落地。驗收：https://tangoatelier.zeabur.app/atelier → 生成骨架 → 最簡版播放 → 切換 D'Arienzo／Di Sarli 對照。

## Context

- Skeleton：`backend/app/engine/skeleton.py` + `catalog.py`
- Render：`backend/app/engine/render.py`（`simple` + Style Profile）
- UI：`frontend/src/pages/AtelierPage.tsx`
- 舊 `/generate/:id` → `/atelier?style=`

## Verify

```bash
curl -sf -X POST https://tangoatelier.zeabur.app/api/skeleton \
  -H 'content-type: application/json' \
  -d '{"dance_type":"tango","key":"A minor","progression_id":"i-iv-V7-i","form_id":"aaba","seed":1}' | head -c 300
```
