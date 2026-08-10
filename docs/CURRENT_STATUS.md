# Current status

**Last updated:** 2026-08-10

## Summary

**TangoAtelier** 主流程：**Skeleton → Style render**。線上：https://tangoatelier.zeabur.app/atelier  

引擎保真度吸收項已全部入 plan（見 `docs/product/PROJECT_PLAN.md` §3b），**尚未逐項實作**；下一刀建議 **E1 樂句終止硬規則**。

## What works

- `POST /api/skeleton`、`POST /api/render`、`GET /api/atelier/options`
- `/atelier`：舞種／key／progression／form → 骨架＋最簡播放 → 樂團風格對照
- Piece motif、phrase 級旋律、drama 弧、violin／cello 分軌（早期）
- 同一 skeleton 下 chord 序列鎖定（已測）

## Known gaps

- §3b E1–E8 引擎保真度 backlog（終止式、A′ 闡述、張力曲線、人性化、表面再和聲、voice leading、配器角色、分層鎖定）
- Vals／Milonga 節奏骨架仍簡化；編制音色未到位
- Hint／Save／Share／參數滑桿未做

## Next steps

1. **E1** 樂句終止硬規則 → 聽感驗收 → **E2** A′ 闡述  
2. 同骨架 D'Arienzo vs Di Sarli 持續對照  
3. 其餘 E-task／產品 Phase 依 `PROJECT_PLAN.md` §4
