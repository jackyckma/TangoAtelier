# Current status

**Last updated:** 2026-08-20

## Summary

**TangoAtelier** 主流程：**Skeleton → Style render**。線上：https://tangoatelier.zeabur.app/atelier  

引擎保真度 **E1–E6、E9–E12** 已落地。音樂模型主線為 **M-task**（見 [`product/MUSICALITY_OVERHAUL.md`](product/MUSICALITY_OVERHAUL.md)）。

**已完成：** M3 → M1 → M2 → **M4（旋律三層重寫）**（人耳驗收 pending）。

**下一刀：** **M10 — Pulse / Groove**（未做），或收斂 M4 警告／KL。

## What works

- Skeleton → simple／orquesta render；phrase cadence；A′ elaboration
- Motivic cells（E11）、結構錨點＋張力（E9）、setup／payoff（E10）
- **M1–M3** as before
- **M4：** `backend/app/engine/melody/` structural → connect（NCT）→ decorate（render）；`DENSITY_MISMATCH`／`RANGE_EXCEEDED` 歸零；leap／rest 進入 DoD 帶

## Known gaps

- **M4 收斂：** interval／duration KL 仍高於 DoD &lt;0.25；`MELODY_NO_REST`／`LEAP_NOT_RECOVERED` 警告未歸零；half+long 偏少
- **M10 Pulse／Groove** — 未做
- M5–M9 as before

## Next steps

1. 人耳驗收 M4
2. M10 或 M4 KL／警告收斂
3. M5+
