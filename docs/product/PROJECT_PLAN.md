# TangoAtelier — Multi-Phase Project Plan

**Last updated:** 2026-08-10  
**Status:** Phase 0–1 已落地；主流程為 **Skeleton → Style render**；引擎保真度 backlog（§3b）待逐項聽驗推進  
**Canonical product spec:** [tango-learning-webapp-project-doc.md](./tango-learning-webapp-project-doc.md)  
**引擎分層規格（研究）：** [../research/Tango_music_synthesis.md](../research/Tango_music_synthesis.md)

本計劃把 product doc 的 Phase 規劃對齊目前決策（Zeabur、MusicXML 主產物、音色、save／share），並納入規則引擎「保真度／多樣性」吸收項——**全部先入 plan，實作分批，每完成一項就聽感驗收再推進**。

---

## 0. 已確認決策

| 決策 | 選擇 |
|------|------|
| 產品名 | TangoAtelier |
| 部署 | GitHub `main` → Zeabur auto-deploy（不維護專案內 Docker Compose） |
| 音樂生成 | 規則引擎（不用 Minimax Music 等音訊黑盒） |
| 中間／匯出格式 | **MusicXML 為主產物**；另產 `.mid` 與 note-event JSON |
| 播放音色 | Tone.js + 高品質 soundfont（先鋼琴；編制層用合成暫代） |
| Phase 0 樂團 | D'Arienzo、Troilo、Di Sarli、Pugliese、Canaro、Biagi |
| 英文文案 | AI 起草，之後人工校 |
| 視覺 | 簡約 + 淡 Latin／artistic，不 fancy |
| Save／Share | **Phase 5**（已確認：不提前做最小版） |
| 生成切法 | **Skeleton（跨樂團鎖定）→ Style render（風格分叉）**；對照教學優先於「一次七層生成」 |

### Skeleton vs Render 過濾器（吸收研究時必守）

| 放 Skeleton（改了就不像「同一首歌」） | 放 Render（改了才像「換樂團」） |
|--------------------------------------|--------------------------------|
| 終止式、主進行、動機 DNA、樂句邊界、曲式段落 | 節奏踩法、闡述密度、織體、局部再和聲、配器角色、微人性化 |
| 主調／段落調性家族 | decoration、相對音量、phrase-end ornament |

研究文件的七層流程**不照抄編號**；內容拆進上表兩欄，再對應 §3b 任務。

---

## 1. 音樂管線（現行）

```
使用者參數（舞種／調／進行／曲式／密度…）
        │
        ▼
Skeleton（Python）—— 跨樂團共用
  • Form 段落時間軸 + drama／energy
  • 和聲進行（section family；之後：樂句終止硬規則）
  • Piece motif + phrase 級旋律
        │
        ├──► Simple render（對照基線）
        │
        ▼
Style render（Style Profile + personality mix）
  • 節奏 pair／articulation／LH 織體
  • 句尾裝飾、可選 A′ 闡述、配器層
  • 微人性化（計劃中）
        │
        ▼
music21 Score → MusicXML + MIDI + note-event JSON
        │
        ▼
Tone.js 播放（鋼琴 soundfont + 暫代 synth 聲部）
```

**為什麼 MusicXML 當主產物？** 保留和弦、聲部、力度、拍號等語意，適合教學與 MuseScore 細修；MIDI／note-event 負責相容下載與前端同步 Hint。

---

## 2. 怎樣避免規則生成太悶？

**結論：材料足夠做「教學上有辨識度、且多次生成不重複」的音樂**——前提是把變化軸做成參數化，而不是寫死幾條 loop。見研究文件第 1–4 節與下表。

| 變化軸 | 來源／例子 | 效果 |
|--------|------------|------|
| 樂團性格 | 四系：節奏／柔情／氣勢／戲劇 | 同一舞曲類型，聽感指紋不同 |
| 節奏骨架 | Marcato en cuatro / en dos、Síncopa、Yumba、Habanera、3+3+2 | 最容易聽出差異的軸 |
| 舞曲類型 | Tango / Vals / Milonga | 拍號與節奏骨架切換 |
| 和聲模板庫 | 順階、下行五度、V7♭9、借用和弦頻率 | 柔情／戲劇系比節奏系更繞 |
| 曲式段落 | intro–A–過渡–B–A'–coda；再現加花 | 避免整首同一個 loop |
| 音色／編制 | 鋼琴 → +吉他 → +bandoneón → 簡化 orchestra | 同骨架不同「衣服」 |
| Articulation | staccato／rubato／留白／動態對比權重 | Biagi「突然空白」、Di Sarli 留白重量感 |
| 隨機種子 | seed 可重現；未鎖定則每次不同 | 同參數也可多次抽樣 |

**「好聽」分兩層：** (1) 編曲／規則 (2) 播放音色。刻意不做 AI 音訊 API 補好聽。

---

## 3. 產品 Phase 路線圖

每個 Phase 結束都要有可獨立驗證的 demo。引擎聽感細項見 **§3b**（可與產品 Phase 交錯推進）。

### Phase 0 — 骨架與內容資料化

**目標：** 網站能瀏覽樂團，資料從 API 來。

- [x] Monorepo、6 Style Profile、FastAPI 列表／詳情、React i18n、基礎視覺
- [x] Zeabur 單 service（root Dockerfile）接 `main`；公開 URL 已上線

**驗收：** 瀏覽器看列表 → 點進樂團看雙語故事；語言可切。

---

### Phase 1 — MVP：生成＋好聽播放（已演進為 Skeleton → Render）

**目標：** 聽到有風格差異的生成段；同一骨架可換風格對照。

- [x] 規則引擎：和聲 + 核心節奏 + form；music21 → MusicXML／MIDI／note-event
- [x] Tone.js + Salamander 鋼琴
- [x] Atelier：skeleton → simple／orquesta render 對照
- [x] Piece motif、phrase 級旋律、drama 弧、violin／cello 分軌（早期版）

**驗收（持續）：** 同骨架下 D'Arienzo vs Di Sarli 節奏／織體可辨；音色不是廉價預設合成器當主力鋼琴。

---

### Phase 2 — 完整曲式、長度、再現闡述

- [ ] 更完整 form：intro–A–過渡–B–過渡–A'–coda（長度約 2–4 分鐘可調）
- [ ] **再現加花** → 主要落在 §3b **E2**（A′ 闡述變形表）
- [ ] 曲式慣例強化（8／16 小節傾向）→ **E0**

**驗收：** 約 3 分鐘曲子有清楚段落對比；A′ 聽得出「同一主題講第二次、更豐富」。

---

### Phase 3 — 舞曲類型與編制

- [ ] Tango／Vals／Milonga 節奏骨架到位（Vals 不繼承 tango 密 16th／32nd）
- [ ] 編制角色：鋼琴 → +吉他 → +bandoneón → 簡化 orchestra（不只開關層）→ **E7**
- [ ] 多軌 Tone.js 音色升級（真實／更好 samples）

**驗收：** 切換舞曲類型節奏正確；切換編制聲部增減與角色合理。

---

### Phase 4 — Hint 視覺化（教學核心）

- [ ] Piano-roll 同步高亮
- [ ] 和弦標記軌（工房已有 bar 級和弦格，可演進）
- [ ] 節奏型態標籤＋白話說明
- [ ] Key 顯示＋「非樂團專屬調」誠實說明

**驗收：** 邊聽邊看 Hint 同步；點節奏標籤看得到解釋。

---

### Phase 5 — 命名、儲存與分享（作品庫）

- [ ] 儲存模型／API／分享頁（見既有清單；**不提前做最小版**除非 founder 改口）

**驗收：** 生成 → 命名儲存 → 分享連結可播放同一首。

---

### Phase 6 — 進階調參與分層鎖定

- [ ] 借用和弦／切分／裝飾／rubato **滑桿**（調各層機率分佈，不是單一「隨機性」旋鈕）
- [ ] **分層鎖定重跑**（鎖和聲只重生節奏／旋律等）→ **E8**
- [ ] MusicXML／MIDI 匯出體驗打磨

**驗收：** 調參後聽感與 Hint 有可見變化；鎖定一層後重跑其他層結果符合預期。

---

### Phase 7（可選，長期）— 意圖建模與統計強化

對應研究文件第 3 節；短曲收益有限，長曲／複雜曲式較有感。

- [ ] 結構錨點雙向填充（簡化版插值即可）→ **E9**
- [ ] 動機 setup／payoff 早排程 → **E10**
- [ ] 內部統計調整機率權重；可解釋模型（如 Markov）評估
- [ ] 與其他探戈工具鏈整合可能性

---

## 3b. 引擎保真度路線（Engine Fidelity）— 逐項聽驗

來源：[Tango_music_synthesis.md](../research/Tango_music_synthesis.md) 吸收項。  
**規則：一次只推進 1–2 個 E-task → commit／deploy → 人耳驗收 → 再下一個。**  
狀態：`pending`｜`in_progress`｜`done`｜`deferred`

共用聽感 checklist（每個 E-task 結束都跑）：

1. 固定 seed：同參數可重現  
2. 同風格 N≥3（理想 ≥10）次生成，彼此不完全像同一首歌  
3. 同 skeleton 下至少對照 D'Arienzo vs Di Sarli（或 Simple vs 一風格）  
4. 若任務動到高潮／密度：高潮小節附近力度／密度／不協和是否高於曲均（可粗統計）

| ID | 任務 | 層 | 對應研究 | 產品 Phase | 狀態 | 聽感驗收重點 |
|----|------|----|----------|------------|------|--------------|
| **E0** | 曲式慣例：段落長度偏 8／16；form 時間軸帶情緒等級 | Skeleton | §2 第一層 | 2 | pending | 段落邊界清楚，不像任意長度拼貼 |
| **E1** | **樂句終止硬規則**（句末傾向 V／V7♭9→i 等）；中段才較自由 | Skeleton | §2 第二層 | 1–2 | done | 樂句「有收束」；仍跨風格共用 |
| **E2** | **A′／再現闡述變形表**（裝飾↑、LH 織體升級、可選局部再和聲、動態↑） | 偏 Render（intent 可標在 Skeleton） | §2 第六層 | 2 | pending | A 與 A′ 像同一故事講兩次，第二次更豐富 |
| **E3** | **張力曲線**當跨層修正（密度／不協和權重／decoration／力度） | Skeleton 目標 + Render 執行 | §3.3 | 2–7 | pending | 高潮／釋放可聽；非突然 dump 密集音 |
| **E4** | **微人性化**：小幅 timing／velocity jitter（幅度之後接滑桿） | Render | §2 第三層 | 3／6 | pending | 少機械量化感；seed 仍可重現 |
| **E5** | **風格表面再和聲**（借用／次屬等）；**不改**共享 chord grid 主幹 | Render | §2 第二／六層 | 2–3 | pending | 同 skeleton 和弦格仍對得上；風格聽感更繞／更直 |
| **E6** | **Voicing 平滑進行**（LH／pads 選 inversion，最小化聲部跳躍） | Render | §2 第四層 | 2–3 | pending | 伴奏較少無意義大跳 |
| **E7** | **配器角色分配**（誰扛節奏、誰對位；吉他／bandoneón 真接手） | Render + 前端音色 | §2 第七層 | 3 | pending | 開關編制時織體角色變，不是只多一層 pad |
| **E8** | **分層鎖定重跑**（固定若干層 seed／輸出，只重抽其他層） | API + UI | §4 | 6 | pending | 「鎖和聲、換節奏」教學場景可用 |
| **E9** | 錨點＋簡化雙向／插值填充（非完整搜尋） | Skeleton＋Render | §3.1–3.2 | 7 | deferred | 長曲敘事更穩；短曲可跳過 |
| **E10** | 動機 setup／payoff 早排程（伏筆→錨點回收） | Skeleton | §3.4 | 7 | deferred | 再現／coda 聽得出「回收」 |

### 建議推進順序（聽感優先）

```
E1 終止式 → E2 A′闡述 → E3 張力曲線
    → E6 voice leading → E5 表面再和聲
    → E4 人性化 → E0 曲式慣例
    → E7 配器角色（搭 Phase 3）
    → E8 分層鎖定（搭 Phase 6）
    → E9 / E10（Phase 7，可選）
```

已部分落地、**不算 E-task 完成**（避免重複開工）：piece motif、phrase 2–4 小節、drama rise／climax／release、violin／cello 分軌、personality mix。後續 E-task 應**接上**這些，不要平行重寫。

---

## 4. 建議實作順序（近期）

1. **現在：** **E1 done** → 下一刀 **E2 A′ 闡述** → **E3 張力曲線**；每項 deploy 後工房聽感驗收  
2. 穿插：同骨架 D'Arienzo vs Di Sarli 對照（產品驗收，不單獨佔 E-id）  
3. Phase 4 Hint、Phase 5 Save／Share 仍依產品優先級；**不阻擋** E1–E3  
4. Phase 6 滑桿／E8、Phase 3／E7 在保真度主線穩定後再加重

---

## 5. 風險與開放問題

| 項目 | 狀態 |
|------|------|
| Zeabur／公開 URL | 已上線 `https://tangoatelier.zeabur.app` |
| Save／Share 是否要帳號 | Phase 5 預設先無帳號輕量方案 |
| 風格再和聲（E5）會否破壞「同骨架對照」 | 必須只動表面層；chord 教學格以 skeleton 為準 |
| Soundfont／弦樂／bandoneón 真 samples | 編制聽感未到位前，規則層與音色層分開評 |
| E9／E10 是否值得做 | 等長曲／複雜 form 有痛點再啟動 |

---

*Phase 與 E-task 範圍可在實作中拆細或合併；以可驗證聽感產出為準，不需死守字面。研究文件若與 Skeleton→Render 衝突，以 §0 過濾器為準。*
