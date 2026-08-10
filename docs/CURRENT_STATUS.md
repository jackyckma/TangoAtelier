# Current status

**Last updated:** 2026-08-10

## Summary

**TangoAtelier** 主流程：**Skeleton → Style render**。線上：https://tangoatelier.zeabur.app/atelier  

引擎保真度：**E1 樂句終止硬規則已落地**（問句→屬、答句→主；中段保留進行模板）。下一刀 **E2 A′ 闡述**。

## What works

- `POST /api/skeleton`、`POST /api/render`、`GET /api/atelier/options`
- `/atelier`：舞種／key／progression／form → 骨架＋最簡播放 → 樂團風格對照
- Piece motif、phrase 級旋律、drama 弧、violin／cello 分軌（早期）
- **Phrase cadence**：chord 可帶 `cadence: half|approach|authentic`；`harmony_plan[].phrases`
- 同一 skeleton 下 chord 序列鎖定（已測）

## Known gaps

- §3b E2–E8（A′ 闡述、張力曲線、人性化、表面再和聲、voice leading、配器角色、分層鎖定）
- Vals／Milonga 節奏骨架仍簡化；編制音色未到位
- Hint／Save／Share／參數滑桿未做

## Next steps

1. 聽感驗收 E1（工房固定 seed，聽樂句收束）→ **E2**  
2. 同骨架 D'Arienzo vs Di Sarli 持續對照  
3. 其餘見 `PROJECT_PLAN.md` §3b／§4
