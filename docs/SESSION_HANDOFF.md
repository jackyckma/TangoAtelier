# Session handoff

**Last updated:** 2026-08-10  
**Branch:** `main`（計劃文件已更新；下一刀實作前再對齊最新 commit）

## Resume here

1. 讀 `docs/product/PROJECT_PLAN.md` **§3b 引擎保真度路線**  
2. 下一實作：**E1 — 樂句終止硬規則**（skeleton；句末 V／V7♭9→i 等）  
3. Done 定義：固定 seed 可重現；樂句有收束感；同 skeleton 風格對照仍成立 → commit／push → 工房聽 → 再開 **E2**

## Context

- 研究規格：`docs/research/Tango_music_synthesis.md`  
- 吸收原則：Skeleton 鎖「同一首歌」；Render 分叉「像哪個樂團」（plan §0 過濾器）  
- Engine：`backend/app/engine/skeleton.py`、`render.py`  
- UI：`frontend/src/pages/AtelierPage.tsx`

## Verified in

- Local：先前 phrase／strings 變更已 push；`scripts/agent-verify.sh` 曾通過  
- Staging：https://tangoatelier.zeabur.app/atelier（聽感持續人工）

## Top priority next

**E1** 樂句終止硬規則（見 PROJECT_PLAN §3b 表）

## How to verify after E1

```bash
bash scripts/agent-verify.sh
# 工房：固定 seed 生成 → 聽樂句收束；換 D'Arienzo／Di Sarli 確認 chord 主幹仍同
```
