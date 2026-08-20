# Current status

**Last updated:** 2026-08-20

## Summary

**TangoAtelier** 主流程：**Skeleton → Style render**。線上：https://tangoatelier.zeabur.app/atelier  

引擎保真度 **E1–E6、E9–E12** 已落地。音樂模型主線為 **M-task**（見 [`product/MUSICALITY_OVERHAUL.md`](product/MUSICALITY_OVERHAUL.md)）。

**已完成：** M3 → M1 → M2 → **M4** → **M10**（已合 `main`）。

**Founder 人耳（2026-08-20）— 主痛點不是「不夠花」，是「變化不服從情緒」：**

1. 變化帶來不適的隨機：句子該延續卻突然停；該穩卻突然一串急音  
2. 全曲連續性弱：像有一個核心旋律 idea，再堆 variation，缺少情緒推進  
3. 和弦也像「刻意換給你聽」，而不是為情緒服務  

**下一刀（改道）：** 先做 **連續性／期待感閘門**（旋律密度・休止・裝飾・中段和弦色彩都跟 drama／tension 走），再進 M6（發展手法服務弧線），再進 **M5**（功能和聲，預設克制、張力才開 colour）。不要先把 M5 做成「更多故意不一樣的和弦」。

## What works

- Skeleton → simple／orquesta render；phrase cadence；A′ elaboration
- Motivic cells（E11）、結構錨點＋張力（E9）、setup／payoff（E10）— **存在但未真正駕馭 M4／和聲變化**
- **M4：** three-pass melody；error 級密度／音域清掉  
- **M10：** pulse／groove_role／chord lag  

## Known gaps

### 音樂模型

- **連續性／期待感（新優先）：** drama／tension_curve 與 M4 rests／density／decorate、中段和弦 colour 脫鉤 → 聽成隨機  
- **M4 收斂：** KL、警告、half+long；人耳「好不好哼」併入連續性刀  
- **M6** 動機發展手法（可教學、跟弧線）  
- **M5** 功能和聲 — 須以情緒／功能為閘，禁止為變化而變化  
- M7–M9 as before  

### 產品面

- Hint／Save／Share／參數滑桿（Phase 4–6）；真實 samples  

## Next steps

1. Spec＋實作「expectancy / continuity gate」（薄任務，可先於完整 M5／M6）  
2. M6 → M5（克制版）→ M7…  
3. 人耳複驗：句子會不會被砍斷、穩段會不會爆密度、和弦是否跟情緒走  
