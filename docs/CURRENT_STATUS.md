# Current status

**Last updated:** 2026-08-09

## Summary

**TangoAtelier** 主流程改為 **Skeleton → Style render**：工房先生成跨樂團共用的曲骨架（調／和聲／曲式／旋律），再以最簡版或各樂團風格渲染同一骨架。線上：https://tangoatelier.zeabur.app/atelier

## What works

- `POST /api/skeleton`、`POST /api/render`、`GET /api/atelier/options`
- `/atelier`：選 Tango／Milonga／Vals、key、progression、form → 骨架＋最簡播放 → 切換樂團 render 對照
- 樂團詳情：故事＋風格參數＋連到工房（預選該風格）
- 同一 skeleton 下 chord 序列鎖定（已測）

## Known gaps

- 仍為鋼琴單聲部；編制音色待後續
- Vals／Milonga 節奏骨架仍簡化
- Hint／Save／Share 未做
- 參數滑桿未做

## Next steps

1. 聽感驗收：同一骨架下 D'Arienzo vs Di Sarli
2. 加強 render 差異／編制音色
