# Current status

**Last updated:** 2026-08-20

## Summary

**TangoAtelier** 主流程：**Skeleton → Style render**。線上：https://tangoatelier.zeabur.app/atelier  

引擎保真度 **E1–E6、E9–E12** 已落地。音樂模型主線改為 **M-task**（見 [`product/MUSICALITY_OVERHAUL.md`](product/MUSICALITY_OVERHAUL.md)）。

**已完成：** M3（critic）→ M1（和聲拼寫）→ M2（樂句和聲 + golden-age 曲式 + 相對調 + A→B V7 bridge）→ **M10（Pulse / Groove；待 founder 人耳驗收）**。

**下一刀：** **M4 — 旋律三層重寫**（可與 M10 人耳驗收平行）。

## What works

- Skeleton → simple／orquesta render；phrase cadence；A′ elaboration
- Motivic cells（E11）、結構錨點＋張力（E9）、setup／payoff（E10）、section groove intent（E12）
- **M1：** 和弦詞彙表；`CHORD_SPELLING_INVALID` 歸零
- **M2：** 樂句終止驅動和聲；`golden_age_short`（60 小節：含 bridge）；B 段相對大小調；`SECTION`／`PHRASE_NO_CADENCE`／`HARMONIC_RHYTHM_ORPHAN` 歸零
- **M3：** hard rules + fingerprint + `musicality-report.py`

## Known gaps

### 音樂模型（剩餘 M-task）

- **M10 已落地（待 founder 人耳）**：`pulse` profile、groove_role 連續 run、chord lag、beat-1 accent、更強 humanize／silence；盲聽驗收仍欠
- **旋律仍偏 contour-first**：缺長音／休止／弱起姿態；`DENSITY_MISMATCH`／`RANGE_EXCEEDED` 仍多 → **M4**
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

1. Founder 人耳驗收 M10（同 skeleton × Di Sarli vs D'Arienzo；B 段連續 drive）
2. **M4** 旋律三層重寫
3. 再進 M5／M6／M7 → M8 → M9
