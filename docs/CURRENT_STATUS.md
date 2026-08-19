# Current status

**Last updated:** 2026-08-19

## Summary

**TangoAtelier** 主流程：**Skeleton → Style render**。線上：https://tangoatelier.zeabur.app/atelier  

引擎保真度 **E1–E6、E9–E12** 已落地。

**2026-08-19 方向調整：** 對 commit `920ddbb` 的實測診斷（60 seeds 統計）發現引擎有結構性的音樂模型問題，不是靠加 E-task 能解決的。主線改為 **M-task 系列**，規格見 [`product/MUSICALITY_OVERHAUL.md`](product/MUSICALITY_OVERHAUL.md)。**下一刀：M3（音樂性 critic）**。

## What works

- Skeleton → simple／orquesta render；phrase cadence（E1）；A′ elaboration（E2）
- **Motivic cells（E11）**：1–3 cells、多種 contour、對比 cell 獨立 roll（非單純倒影）
- **E9** structural anchors＋張力插值；**E10** motif setup／payoff 早排程
- **E12** section groove intent（intro 疏／A 立住／B 加深 colour／coda 收）
- **選中進行會在 A／A′／B 循環**；intro／bridge／coda 才強制終止。Vals 樂句可長至 8–12 小節。

## Known gaps

### 音樂模型（M-task 主線）

- **和弦拼寫 bug**：`harmony.py` 一律用和聲小調求根音 → A 小調的 `VII` = G#–C–Eb（應為 G–B–D）。`descending_fifths` 抽中率 1/3 → M1
- **`iiø` 缺七音**：生成減三和弦 B–D–F，標籤與聲響不符 → M1
- **和聲循環與段落長度不對齊**：8 小節循環 vs 12 小節 A 段 → 段落結束在非終止和弦 → M2
- **旋律 contour-first**：音程 98% 為級進、每小節 1.84 音、無長音、無休止、同音重複被主動消滅 → M4
- **和弦詞彙不足**：15 種符號，i/V7/I 佔 70%；無次屬、減七、bII、增六、半音低音線 → M5
- **多樣性在音符層而非計劃層**：每個 seed 都是同一個 36 小節宏觀形狀 → M7
- **配器只是換音量**：bandoneón 永遠 pad、弦樂永遠長音，無旋律交接、無 contracanto、無 variación 段 → M8

### 產品面

- Vals／Milonga 節奏仍簡化；真實 samples 未到位（bandoneón 尤其關鍵）
- Hint／Save／Share／參數滑桿未做

## E-task 與 M-task 的關係

已完成的 E-task 成果保留，在新架構中的對應位置：

| E-task | 在 M-task 中的位置 |
|---|---|
| E2（A′ 闡述） | M6 的 `A_prime` 手法表 |
| E9（結構錨點） | M7 的 tension shape |
| E11（motivic cells） | M4 的 PitchCell／RhythmCell（拆成音高與節奏兩份） |

未完成的 E-task 已被涵蓋：**E0 → M2**、**E7 → M8**、**E8 → M9**。

## Next steps

1. **M3 — 音樂性 critic 與統計指紋**（先做；沒有測量工具，後續改動無法驗證）
2. M1 — 和聲拼寫修正與和弦詞彙表
3. M2 — 樂句驅動的和聲規劃

完整順序與 DoD 見 [`product/MUSICALITY_OVERHAUL.md`](product/MUSICALITY_OVERHAUL.md) §3。
