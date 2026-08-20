# Current status

**Last updated:** 2026-08-20

## Summary

**TangoAtelier** 主流程：**Skeleton → Style render**。線上：https://tangoatelier.zeabur.app/atelier  

引擎保真度 **E1–E6、E9–E12** 已落地。音樂模型主線為 **M-task**（見 [`product/MUSICALITY_OVERHAUL.md`](product/MUSICALITY_OVERHAUL.md)）。

**已完成：** M3 → M1 → M2 → **M4（旋律三層重寫）** → **M10（Pulse / Groove）**（兩者人耳驗收 pending）。

**下一刀：** 人耳驗收 M4＋M10；收斂 M4 警告／KL；再進 **M5**。

## What works

- Skeleton → simple／orquesta render；phrase cadence；A′ elaboration
- Motivic cells（E11）、結構錨點＋張力（E9）、setup／payoff（E10）
- **M1–M3** as before
- **M4：** `backend/app/engine/melody/` structural → connect（NCT）→ decorate（render）；`DENSITY_MISMATCH`／`RANGE_EXCEEDED` 歸零；leap／rest 進入 DoD 帶
- **M10：** `groove.py` + profile `pulse`；`groove_role` 連續 contrast run；chord lag／beat-1 accent／humanize

## Known gaps

### 音樂模型（剩餘 M-task）

- **M4 收斂：** interval／duration KL 仍高於 DoD &lt;0.25；`MELODY_NO_REST`／`LEAP_NOT_RECOVERED` 警告未歸零；half+long 偏少；人耳「好不好哼」pending
- **M10 人耳 pending：** 同 skeleton × Di Sarli vs D'Arienzo 踩法差；B 段連續 drive 是否可數
- **功能和聲語法**尚未取代固定 progression 池 → M5
- **動機發展手法表**（可教學）→ M6
- **Archetype 宏觀多樣性** → M7
- **配器角色 + variación + bandoneón sample** → M8
- **教學 IR／逐層剝開** → M9

### 產品面

- Vals／Milonga 節奏仍簡化；真實 samples 未到位
- Hint／Save／Share／參數滑桿未做（Phase 4–6）

## Skeleton vs Render（Pulse 決策）

Pulse／groove **主要在 Render**：同一 skeleton 換樂團＝換踩法（D'Arienzo 推著走 vs Di Sarli／Pugliese 心跳與戲劇）。Skeleton 只保留 drama／section_groove **意圖**與可數的拍號格子。詳見 overhaul **§M10**。

## Next steps

1. Founder 人耳驗收 M4（旋律）＋ M10（舞池／B 段換格）
2. 可選收斂 M4 KL／警告
3. 再進 M5／M6／M7 → M8 → M9
