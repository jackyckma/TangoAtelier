# TangoAtelier — Multi-Phase Project Plan

**Last updated:** 2026-08-09  
**Status:** Phase 1 implemented — rule engine + generator UI + Salamander piano playback  
**Canonical product spec:** [tango-learning-webapp-project-doc.md](./tango-learning-webapp-project-doc.md)

本計劃把 product doc 的 Phase 規劃對齊目前決策（Zeabur、MusicXML 主產物、音色、save／share），並補充「規則引擎如何避免太悶」的設計方針。

---

## 0. 已確認決策

| 決策 | 選擇 |
|------|------|
| 產品名 | TangoAtelier |
| 部署 | GitHub `main` → Zeabur auto-deploy（不維護專案內 Docker Compose） |
| 音樂生成 | 規則引擎（不用 Minimax Music 等音訊黑盒） |
| 中間／匯出格式 | **MusicXML 為主產物**；另產 `.mid` 與 note-event JSON |
| 播放音色 | Tone.js + 高品質 soundfont（先鋼琴） |
| Phase 0 樂團 | D'Arienzo、Troilo、Di Sarli、Pugliese、Canaro、Biagi |
| 英文文案 | AI 起草，之後人工校 |
| 視覺 | 簡約 + 淡 Latin／artistic，不 fancy |
| Save／Share | **Phase 5**（已確認：不提前做最小版） |

---

## 1. 音樂管線（規則引擎怎麼產出）

```
Style Profile + 使用者參數
        │
        ▼
規則引擎（Python）
  • 選 key / 曲式段落 / 和聲進行
  • 套節奏骨架（Marcato / Síncopa / Habanera / 3+3+2…）
  • 寫旋律骨架 + 裝飾（依樂團 articulation 權重）
  • 依編制填聲部
        │
        ▼
music21 Score（記憶體內的「樂譜物件」）
        │
        ├──► MusicXML  （主產物：可進 MuseScore、可再編輯、語意完整）
        ├──► MIDI (.mid)（相容下載、部分 DAW）
        └──► note-event JSON + chord／rhythm 標記（前端 Tone.js 播放 + Hint）
```

**為什麼 MusicXML 當主產物？**

- 保留和弦、聲部、力度、拍號等語意，比「只存 MIDI」更適合教學與後續編輯。
- 使用者之後可下載進 MuseScore 細修（個人學習價值高）。
- MIDI 仍保留：相容性好、檔小、部分流程需要。

**前端播放不直接「渲染 XML 成聲」**——而是用同一份 Score 匯出的 note-event JSON，交給 Tone.js + soundfont 即時播放，才能做同步 Hint。

---

## 2. 怎樣避免規則生成太悶？材料夠不夠？

**結論：材料足夠做「教學上有辨識度、且多次生成不重複」的音樂**——前提是把變化軸做成參數化，而不是寫死幾條 loop。

研究文件（`docs/research/`）已提供可結構化的「樂句庫原料」：

| 變化軸 | 來源／例子 | 效果 |
|--------|------------|------|
| 樂團性格 | 四系：節奏／柔情／氣勢／戲劇 | 同一舞曲類型，聽感指紋不同 |
| 節奏骨架 | Marcato en cuatro / en dos、Síncopa、Yumba、Habanera、3+3+2 | 最容易聽出差異的軸 |
| 舞曲類型 | Tango / Vals / Milonga | 拍號與節奏骨架切換 |
| 和聲模板庫 | 順階 I–IV–V、下行五度、V7♭9、借用和弦頻率 | 柔情／戲劇系比節奏系更繞 |
| 曲式段落 | intro–A–過渡–B–A'–coda；再現加花 | 避免整首同一個 loop |
| 音色／編制 | 鋼琴 → +吉他 → +bandoneón → 簡化 orchestra | 同骨架不同「衣服」 |
| Articulation | staccato／rubato／留白／動態對比權重 | Biagi「突然空白」、Di Sarli 留白重量感 |
| 隨機種子 | seed 可重現；未鎖定則每次不同 | 同參數也可多次抽樣 |

**「好聽」分兩層，不要混在一起：**

1. **編曲／規則層** — 節奏對比、段落對比、從簡到繁；目標是「像該樂團的教學範例」，不是取代真人作曲。
2. **播放音色層** — 即使用簡單編曲，差的合成器會讓一切變悶；Phase 1 就要上像樣的鋼琴 soundfont。

**刻意不做的（避免假豐富）：** 用 AI 音訊 API 補「好聽」——會犧牲 Hint／可解釋／版權邊界。

**材料缺口（之後補，不擋 MVP）：**

- 節奏 pattern 函式庫要先寫核心 3–5 種，再擴充。
- 旋律是「骨架 + 動機變奏」，不是曲調資料庫（避免像原曲）。
- 英文 bio／術語對照由 AI 起草後校訂。

---

## 3. Phase 路線圖

每個 Phase 結束都要有可獨立驗證的 demo。建議每 Phase 一條 `feat/phase-N-*` branch，合進 `main` 後由 Zeabur 自動部署。

### Phase 0 — 骨架與內容資料化

**目標：** 網站能瀏覽樂團，資料從 API 來；尚無生成。

- [x] Monorepo：`frontend/`、`backend/`（Zeabur 用兩個 service；本機用各自 dev server）
- [x] 6 個 Style Profile JSON（雙語）：D'Arienzo、Troilo、Di Sarli、Pugliese、Canaro、Biagi
- [x] FastAPI：`GET /health`、`GET /api/orchestras`、`GET /api/orchestras/{id}`
- [x] React：首頁、樂團列表（樂團／性格雙路徑）、樂團詳情；i18n 中英切換
- [x] 簡約 Latin／artistic 基礎視覺（CSS variables、字體）
- [x] 根 README、`.env.example`、基礎 verify 指令
- [ ] 瀏覽器驗收＋Zeabur 兩個 service 接上 `main`

**驗收：** 瀏覽器看列表 → 點進樂團看雙語故事；語言可切；資料來自後端。

---

### Phase 1 — MVP：鋼琴生成＋好聽播放

**目標：** 選樂團 → 生成 → 聽到有風格差異的鋼琴段。

- [x] 規則引擎 v1：和聲進行 + Marcato／Síncopa 等核心節奏；intro–A–A'–coda（約 1–2 分鐘）
- [x] music21 Score → MusicXML + `.mid` + note-event JSON
- [x] `POST /api/generate`（參數：orchestra_id、可選 seed）
- [x] 前端 Tone.js + **高品質鋼琴 soundfont**（Salamander）
- [x] 生成器頁雛形：選樂團 → 生成 → 播放／暫停；可下載 `.mid`／MusicXML

**驗收：** D'Arienzo vs Di Sarli 節奏聽感明顯不同；音色不是廉價預設合成器。

---

### Phase 2 — 完整曲式與長度

- [ ] intro–A–過渡–B–過渡–A'–coda
- [ ] 長度參數（約 2–4 分鐘）
- [ ] 再現加花（從簡到繁）

**驗收：** 約 3 分鐘曲子有清楚段落對比。

---

### Phase 3 — 舞曲類型與編制

- [ ] Tango / Vals / Milonga 節奏骨架
- [ ] 編制：鋼琴 → +吉他 → +bandoneón → 簡化 orchestra
- [ ] 多軌 Tone.js 音色

**驗收：** 切換舞曲類型節奏正確；切換編制聲部增減正確。

---

### Phase 4 — Hint 視覺化（教學核心）

- [ ] Piano-roll 同步高亮
- [ ] 和弦標記軌
- [ ] 節奏型態標籤＋白話說明
- [ ] Key 顯示＋「非樂團專屬調」誠實說明

**驗收：** 邊聽邊看 Hint 同步；點節奏標籤看得到解釋。

---

### Phase 5 — 命名、儲存與分享（作品庫）

**目標：** 生成結果不是 one-off——使用者可命名、存到伺服器、用連結分享。

- [ ] 儲存模型：標題、orchestra、參數、seed、MusicXML（或儲存路徑）、可選 note-event 快取、建立時間
- [ ] API：建立／讀取／列表公開作品；分享用短 ID 或 slug URL
- [ ] UI：生成後「命名並儲存」；「我的作品／探索」簡易列表；公開分享頁可播放
- [ ] 第一版可用輕量方案（無完整帳號）：例如瀏覽器 local identity + 可選顯示名稱；完整帳號系統列為後續加分
- [ ] 版權／濫用：只存生成物與參數，不存原曲；基本 rate limit

**驗收：** 使用者生成 → 命名儲存 → 開另一裝置／無痕用分享連結能播放同一首。

---

### Phase 6 — 進階調參與匯出強化

- [ ] 借用和弦／切分／裝飾／rubato 滑桿
- [ ] 鎖定和聲骨架、只重生節奏（或相反）
- [ ] MusicXML／MIDI 匯出體驗打磨（已在 Phase 1 有基礎）

**驗收：** 調參後聽感與 Hint 有可見變化。

---

### Phase 7（可選，長期）— 統計特徵強化規則

- [ ] 用內部分析調整機率權重（不重製旋律）
- [ ] 評估可解釋的統計模型（如 Markov）補強規則
- [ ] 與其他探戈工具鏈整合可能性

---

## 4. 建議實作順序（近期）

1. **現在：** scaffolding 已落地；push `main` → founder 接 Zeabur → 提供 project ID／URL  
2. **下一步：** Phase 0（骨架＋6 樂團資料）  
3. 然後 Phase 1（生成＋音色）——這是第一個「有聲音」的里程碑  
4. Phase 4（Hint）與 Phase 5（Save／Share）都是體驗核心；順序上 Hint 先於作品庫較合理（分享時已有可看的教學介面），但若你想更早有「可分享作品」，可在 Phase 1 後做一個 **最小 Save（只存 MusicXML＋參數＋分享連結）**，Hint 稍後再疊——實作前再確認一次即可。

---

## 5. 風險與開放問題

| 項目 | 狀態 |
|------|------|
| Zeabur project ID／公開 URL | 等 founder 接好 GitHub integration 後提供 |
| Save／Share 是否要帳號 | Phase 5 預設先無帳號輕量方案；要不要 Google login 等你之後定 |
| Phase 1 後是否插入「最小 Save」 | 開放——見 §4 |
| Soundfont 授權與打包方式（CDN vs 自架靜態） | Phase 1 實作時選定 |

---

*Phase 範圍可在實作中拆細或合併；以可驗證產出為準，不需死守字面。*
