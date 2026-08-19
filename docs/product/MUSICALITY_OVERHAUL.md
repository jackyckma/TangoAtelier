# TangoAtelier — 音樂性改造實作規格（Musicality Overhaul）

**版本：** 1.0
**建立日期：** 2026-08-19
**目標讀者：** Cursor AI（實作）＋ founder（聽感驗收）
**對應現有文件：** `docs/product/PROJECT_PLAN.md`（E-task 路線）、`docs/research/Tango_music_synthesis.md`

---

## 0. 這份文件怎麼用

本文件定義 **M-task（Musicality task）** 系列，與現有的 E-task 並行但層級更根本：E-task 是在現有架構上加功能，M-task 是**修正架構本身的音樂模型**。

**執行規則（沿用專案既有慣例）：**

1. 一次只推進 **1 個 M-task**
2. 每個 M-task 完成後：跑 `tests/musicality/` → commit → deploy → founder 人耳驗收 → 才進下一個
3. 每個 M-task 都有明確的「完成定義（DoD）」與「不要做的事」
4. **禁止**在同一個 commit 裡混合兩個 M-task
5. 若某個 M-task 的驗收失敗，先回滾再重做，不要疊補丁

**M-task 依賴圖：**

```
M1 (和聲拼寫修正) ──┐
M2 (樂句驅動和聲) ──┼──► M4 (旋律三層重寫) ──► M6 (動機發展手法)
M3 (音樂性 critic) ─┘                          │
                                                ▼
M5 (功能和聲語法) ──────────────────────► M7 (Archetype 多樣性)
                                                │
                                                ▼
                                    M8 (配器角色) ──► M9 (教學 IR + UI)
```

M1、M2、M3 可平行；M3 建議**最先做**，因為它是後續所有改動的驗收工具。

---

## 1. 問題診斷摘要（為什麼要做這些改動）

以下是對 commit `920ddbb` 的實測結果（60 seeds，dance_type=tango，約 5000 個旋律音程）：

| 指標 | 實測值 | 應有的樣子 | 問題 |
|---|---|---|---|
| 音程分佈 | 0/±1/±2/±3/±4 佔 98%；≥5 半音僅 83 次 | 探戈開句常見 6 度、8 度大跳後級進回填 | 旋律是音階爬行，沒有姿態 |
| 每小節主旋律音數 | 1.84（density=medium 目標為 5） | 隨 density 參數變動 | 密度參數失效 |
| 起音位置分佈 | 0.5 拍(1322) > 0.0 拍(1179)；1.5 拍僅 247 | 弱起應成系統，切分應對抗左手 | 無 anacrusis、無真正切分 |
| 時值分佈 | 全部集中 0.25–0.5 拍 | 應有 ≥2 拍長音作為呼吸 | 沒有「唱」的感覺 |
| 同音重複 | 程式碼主動消滅（`# Kill remaining unisons`） | declamación 是探戈旋律核心手法 | 把特徵當 bug 修掉 |
| 和弦詞彙 | 15 種符號，i/V7/I 佔 70% | 次屬、減七、bII、增六、m6、半音低音線 | 詞彙量不足以支撐風格 |
| 宏觀形狀 | 每個 seed 都是 36 小節 intro4-A12-bridge4-A'12-coda4 | 應在計劃層抽樣 | 「換 seed = 換配音」 |

**三個確定的 bug：**

1. `harmony.py::_root_for_degree()` 一律用 `HARMONIC_MINOR` 求根音 → A 小調的 `VII` 生成 **G#–C–Eb**（應為 G–B–D）。`descending_fifths` 是 3 個小調進行之一，抽中率 1/3。
2. `iiø` 用 `TRIAD_DIM` 生成 B–D–F（減三和弦），**缺七音**，標籤與聲響不符。
3. `bars_per_chord=2` × 4 和弦 = 8 小節循環，但 A 段 12 小節 → 段落結束在非終止和弦（實測 seed 7 的 A 段結束在 `iv`）。

---

## 2. M-task 規格

---

### M3 — 音樂性 Critic 與統計指紋（**建議先做**）

**層級：** 測試基礎設施
**依賴：** 無
**預估：** 中

#### 動機

目前沒有任何自動化的音樂品質檢查。每次改動都靠人耳抽查 N 個 seed，成本高且不可靠。M3 把「聽起來怪」變成可測量的數字，後續所有 M-task 都靠它驗收。

#### 新增檔案

```
backend/app/critic/
├── __init__.py
├── rules.py          # 硬規則檢查
├── fingerprint.py    # 統計指紋比對
├── report.py         # 產生可讀報告
└── reference/
    └── golden_age.json   # 參考統計（見下）

backend/tests/musicality/
├── test_hard_rules.py
├── test_fingerprint.py
└── conftest.py
```

#### 2.1 硬規則（`critic/rules.py`）

實作 `check_hard_rules(skeleton: dict, rendered: dict | None = None) -> list[Violation]`。

```python
@dataclass
class Violation:
    rule_id: str          # "CADENCE_UNRESOLVED"
    severity: str         # "error" | "warning"
    bar: int | None
    detail: str
```

必須實作的規則：

| rule_id | severity | 檢查內容 |
|---|---|---|
| `CHORD_SPELLING_INVALID` | error | 生成的和弦音集合是否落在該調的合法和弦詞彙表內（M1 會建立這張表） |
| `SECTION_NO_CADENCE` | error | 每個 A/B/A_prime 段落的最後一個和弦必須是 i/I（完全終止）或 V/V7（半終止），不得是 iv/IV/VI 等 |
| `PHRASE_NO_CADENCE` | warning | 每個樂句末的和弦應落在終止式清單內 |
| `LEAP_NOT_RECOVERED` | warning | 旋律跳進 ≥5 半音後，下一個音應反方向級進（容許 20% 例外） |
| `MELODY_NO_LONG_NOTE` | warning | 每個 8 小節窗口內至少要有一個 ≥1.5 拍的旋律音 |
| `MELODY_NO_REST` | warning | 每個樂句至少要有一次 ≥1 拍的休止 |
| `LH_PARALLEL_FIFTHS` | warning | 左手相鄰兩次 block 攻擊之間的平行五度／八度（同向） |
| `RANGE_EXCEEDED` | error | 旋律超出 `MELODY_LO..MELODY_HI`；左手超出 28..60 |
| `DENSITY_MISMATCH` | error | 實際每小節旋律音數與 `DENSITY_NOTES_PER_BAR` 目標值偏差 > 40% |
| `HARMONIC_RHYTHM_ORPHAN` | warning | 和聲循環未在段落邊界完成一整圈 |

#### 2.2 統計指紋（`critic/fingerprint.py`）

```python
def extract_fingerprint(skeleton: dict) -> Fingerprint:
    """從生成結果抽出可比對的統計分佈。"""

@dataclass
class Fingerprint:
    interval_hist: dict[int, float]      # 音程 → 機率（-12..+12，超出歸入 bucket）
    onset_hist: dict[float, float]       # 小節內起音位置 → 機率
    duration_hist: dict[str, float]      # 時值類別（16th/8th/quarter/half/長）→ 機率
    chord_transition: dict[str, dict[str, float]]  # 和弦轉移矩陣
    notes_per_bar: float
    rest_ratio: float                    # 沒有旋律音的小節比例
    repeated_note_ratio: float
    leap_ratio: float                    # |interval| >= 5 的比例
```

比對用 **KL divergence**：

```python
def compare(fp: Fingerprint, ref: Fingerprint) -> dict[str, float]:
    """回傳每個維度的 KL divergence。"""
```

#### 2.3 參考統計來源（`critic/reference/golden_age.json`）

**重要：只使用公有領域或明確授權的素材。** 建議來源優先序：

1. 已進入公有領域的探戈樂譜（1930 年前出版者，依所在地法規確認）
2. 手動建立的「專家先驗（expert prior）」——若素材取得困難，**先用人工設定的目標分佈**，這已經足以抓出當前的偏差

先用專家先驗，數值如下（tango，可依聽感調整）：

```json
{
  "tango": {
    "interval_hist": {
      "0": 0.14, "1": 0.10, "-1": 0.11, "2": 0.13, "-2": 0.14,
      "3": 0.06, "-3": 0.06, "4": 0.045, "-4": 0.045,
      "5": 0.035, "-5": 0.035, "7": 0.025, "-7": 0.025,
      "8": 0.008, "-8": 0.008, "9": 0.006, "-9": 0.006,
      "12": 0.005, "-12": 0.005
    },
    "onset_hist": { "0.0": 0.30, "0.5": 0.20, "0.75": 0.10, "1.0": 0.22, "1.5": 0.13, "1.75": 0.05 },
    "duration_hist": { "sixteenth": 0.12, "eighth": 0.34, "quarter": 0.30, "half": 0.16, "long": 0.08 },
    "notes_per_bar": 3.2,
    "rest_ratio": 0.18,
    "repeated_note_ratio": 0.14,
    "leap_ratio": 0.16
  }
}
```

vals / milonga 各自一組（vals `notes_per_bar` 較低約 2.4、`leap_ratio` 較高約 0.20；milonga `onset_hist` 集中在 0.0/0.75/1.5）。

#### 2.4 測試

```python
# tests/musicality/test_hard_rules.py
@pytest.mark.parametrize("dance", ["tango", "vals", "milonga"])
@pytest.mark.parametrize("seed", range(1, 51))
def test_no_error_violations(dance, seed):
    sk = build_skeleton(dance_type=dance, seed=seed)
    errors = [v for v in check_hard_rules(sk) if v.severity == "error"]
    assert not errors, format_violations(errors)
```

```python
# tests/musicality/test_fingerprint.py
def test_fingerprint_within_tolerance():
    fps = [extract_fingerprint(build_skeleton(dance_type="tango", seed=s))
           for s in range(1, 101)]
    agg = aggregate(fps)
    kl = compare(agg, load_reference("tango"))
    assert kl["interval_hist"] < 0.25, f"旋律音程分佈偏離參考: {kl}"
    assert kl["onset_hist"] < 0.20
    assert kl["duration_hist"] < 0.25
```

**注意：這些測試在 M3 剛完成時「應該是失敗的」** —— 這正是它們的價值。做法：

- M3 完成時，把 threshold 設為**當前實測值**，並在測試檔頂端加註 `# BASELINE 2026-08-19: interval_hist KL = 0.71`
- 每完成一個 M-task，收緊 threshold，並記錄新的 baseline
- 加一個 `scripts/musicality-report.py` 輸出對照表，方便 founder 看進度

#### 新增 CLI

```bash
python scripts/musicality-report.py --dance tango --seeds 100
```

輸出：硬規則違規統計、各維度 KL、以及與上次 baseline 的對照。

#### DoD

- [ ] `pytest tests/musicality/` 可跑，且輸出人類可讀的違規清單
- [ ] `scripts/musicality-report.py` 能產生 tango/vals/milonga 三份報告
- [ ] baseline 數值記錄在 `docs/musicality-baseline.md`
- [ ] 報告確認能偵測到本文件 §1 列出的所有問題

#### 不要做的事

- 不要在 M3 修任何生成邏輯。M3 只負責「測量」。

---

### M1 — 和聲拼寫修正與和弦詞彙表

**層級：** Skeleton / harmony
**依賴：** 無（建議 M3 之後做，以便驗證）
**預估：** 小

#### 動機

修正 §1 列出的 bug 1 與 bug 2，並建立一張**明確的和弦詞彙表**作為後續 M5 的基礎。

#### 檔案

- 重寫 `backend/app/engine/harmony.py`
- 新增 `backend/app/engine/harmony_vocab.py`

#### 1.1 和弦詞彙表（`harmony_vocab.py`）

用「明確定義每個和弦」取代「從音階算根音」。這消滅整類 bug。

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class ChordSpec:
    symbol: str            # "bVII"
    root_semitones: int    # 相對主音的半音數
    intervals: tuple[int, ...]   # 相對根音
    function: str          # "tonic" | "subdominant" | "dominant" | "passing" | "colour"
    label_zh: str
    label_en: str

MINOR_VOCAB: dict[str, ChordSpec] = {
    # --- 順階三和弦 ---
    "i":     ChordSpec("i",     0,  (0,3,7),     "tonic",       "主和弦",       "tonic minor"),
    "iiø7":  ChordSpec("iiø7",  2,  (0,3,6,10),  "subdominant", "半減七",       "half-diminished 7th"),
    "ii°":   ChordSpec("ii°",   2,  (0,3,6),     "subdominant", "二級減三",     "diminished triad"),
    "III":   ChordSpec("III",   3,  (0,4,7),     "tonic",       "關係大三",     "relative major"),
    "III+":  ChordSpec("III+",  3,  (0,4,8),     "colour",      "增三和弦",     "augmented"),
    "iv":    ChordSpec("iv",    5,  (0,3,7),     "subdominant", "下屬小三",     "minor subdominant"),
    "iv6":   ChordSpec("iv6",   5,  (0,3,7,9),   "subdominant", "下屬小六",     "minor 6th"),
    "IV":    ChordSpec("IV",    5,  (0,4,7),     "subdominant", "大下屬（多利安色彩）", "major IV (dorian)"),
    "v":     ChordSpec("v",     7,  (0,3,7),     "dominant",    "自然小五級",   "natural minor v"),
    "V":     ChordSpec("V",     7,  (0,4,7),     "dominant",    "屬和弦",       "dominant"),
    "V7":    ChordSpec("V7",    7,  (0,4,7,10),  "dominant",    "屬七",         "dominant 7th"),
    "V7b9":  ChordSpec("V7b9",  7,  (0,4,7,10,13),"dominant",   "屬七降九",     "dominant 7♭9"),
    "VI":    ChordSpec("VI",    8,  (0,4,7),     "subdominant", "六級大三",     "submediant major"),
    "bVII":  ChordSpec("bVII",  10, (0,4,7),     "subdominant", "降七級大三",   "flat-VII"),
    "vii°7": ChordSpec("vii°7", 11, (0,3,6,9),   "dominant",    "導七減七",     "fully-diminished 7th"),

    # --- 次屬和弦（探戈核心詞彙） ---
    "V7/iv": ChordSpec("V7/iv", 0,  (0,4,7,10),  "dominant",    "iv 的次屬",    "secondary dom of iv"),
    "V7/V":  ChordSpec("V7/V",  2,  (0,4,7,10),  "dominant",    "V 的次屬",     "secondary dom of V"),
    "V7/VI": ChordSpec("V7/VI", 3,  (0,4,7,10),  "dominant",    "VI 的次屬",    "secondary dom of VI"),
    "V7/III":ChordSpec("V7/III",10, (0,4,7,10),  "dominant",    "III 的次屬",   "secondary dom of III"),

    # --- 色彩／半音和弦 ---
    "bII":   ChordSpec("bII",   1,  (0,4,7),     "subdominant", "拿坡里",       "Neapolitan"),
    "Ger+6": ChordSpec("Ger+6", 8,  (0,4,7,10),  "dominant",    "德式增六",     "German augmented 6th"),
    "It+6":  ChordSpec("It+6",  8,  (0,4,10),    "dominant",    "義式增六",     "Italian augmented 6th"),
    "subV7": ChordSpec("subV7", 1,  (0,4,7,10),  "dominant",    "三全音替代",   "tritone substitute"),
    "i6":    ChordSpec("i6",    0,  (0,3,7,9),   "tonic",       "小六和弦",     "minor 6th"),
    "iM7":   ChordSpec("iM7",   0,  (0,3,7,11),  "tonic",       "小大七",       "minor-major 7th"),
    "i7":    ChordSpec("i7",    0,  (0,3,7,10),  "tonic",       "小七",         "minor 7th"),
    "I":     ChordSpec("I",     0,  (0,4,7),     "tonic",       "畢卡第三音",   "Picardy third"),
}

MAJOR_VOCAB: dict[str, ChordSpec] = { ... }  # 同樣風格，含 iv（借用小下屬）、bVI、bIII、V7/ii 等
```

#### 1.2 重寫 `chord_pitches()`

```python
def chord_pitches(tonic: int, mode: str, symbol: str, *, inversion: int = 0,
                  octave_shift: int = 0) -> list[int]:
    vocab = MINOR_VOCAB if mode == "minor" else MAJOR_VOCAB
    spec = vocab.get(symbol)
    if spec is None:
        raise UnknownChordSymbol(f"{symbol} not in {mode} vocabulary")
    root = tonic + spec.root_semitones + octave_shift * 12
    pitches = [root + iv for iv in spec.intervals]
    return apply_inversion(pitches, inversion)
```

**移除** `_root_for_degree()`、`_quality_for()`、`_degree_for()`。它們是 bug 的來源。

#### 1.3 遷移既有進行

`catalog.py` 與 `harmony.py` 裡的進行定義要用新符號重寫：

```python
PROGRESSIONS_MINOR = {
    "i-iv-V7-i":         ["i", "iv", "V7", "i"],
    "i-VI-III-V7":       ["i", "VI", "III", "V7"],
    "descending_fifths": ["i", "iv", "bVII", "III", "VI", "iiø7", "V7", "i"],   # ← bVII 修正
    # 新增（M5 之前先用固定模板讓詞彙上線）
    "chromatic_bass":    ["i", "iM7", "i7", "i6", "iv", "V7", "i", "i"],
    "neapolitan_cadence":["i", "iv", "bII", "V7", "i"],
    "secondary_dominant":["i", "V7/iv", "iv", "V7/V", "V7", "i"],
    "picardy_close":     ["i", "iv", "V7b9", "i", "iv", "V7", "I"],
}
```

#### 1.4 相容性

- `_TO_MAJOR` / `_TO_MINOR` 映射表要更新以涵蓋新符號
- `render.py::_surface_reharm_symbol()` 已在用 `V7b9`，確認新詞彙表有它（有）
- `export_formats.py` 目前不輸出和弦符號到 MusicXML —— **順便加上 `<harmony>` 元素**，用 `ChordSpec.symbol` 與 `label_en`。這對教學用途很重要（MuseScore 打開時會顯示和弦記號）

#### DoD

- [ ] `CHORD_SPELLING_INVALID` 違規歸零
- [ ] 手動驗證：A 小調的 `bVII` = G–B–D，`iiø7` = B–D–F–A，`bII` = Bb–D–F
- [ ] MusicXML 輸出含 `<harmony>` 和弦記號，MuseScore 可正確顯示
- [ ] 既有 API 契約不變（`/api/skeleton` 回傳的 `chords[].symbol` 可能改字串，前端需同步）

---

### M2 — 樂句驅動的和聲規劃

**層級：** Skeleton / form + harmony
**依賴：** M1
**預估：** 中

#### 動機

修正 §1 bug 3。根因是因果關係顛倒：現在是「和弦循環填滿小節」，應該是「樂句決定終止，終止決定和弦」。

#### 檔案

- 新增 `backend/app/engine/form.py`
- 修改 `skeleton.py`：移出 `_plan_section_harmony`、`_partition_phrases`、`_apply_phrase_cadences`

#### 2.1 曲式資料結構

```python
@dataclass
class Phrase:
    index: int              # 在段落內的序號 0..n-1
    bar_from: int           # 1-based
    bars: int               # 通常 4，vals 可 8
    cadence: str            # "half" | "imperfect" | "deceptive" | "authentic" | "open"
    role: str               # "question" | "answer"
    anacrusis_beats: float  # 弱起佔前一小節的拍數，0 = 從強拍開始

@dataclass
class Section:
    name: str               # "intro" | "A" | "B" | "A_prime" | "coda" | "variacion"
    bar_from: int
    bars: int
    phrases: list[Phrase]
    key: str
    mode: str
    tonic: int
    energy: float           # 0..1，段落層級的情緒等級
```

#### 2.2 終止式分級規則（**這是本 task 的核心**）

一個 16 小節段落 = 4 個樂句，終止式必須形成敘事：

| 樂句 | 終止式 | 和聲落點 | 效果 |
|---|---|---|---|
| 1（問） | `half` | V 或 V7 | 開啟懸念 |
| 2（答） | `imperfect` | i，但旋律不落在主音（落 3 音或 5 音） | 部分解決，仍想繼續 |
| 3（問） | `deceptive` 或 `half` | V→VI，或再次停在 V7 | 加深張力 |
| 4（答） | `authentic` | V7(b9)→i，旋律落主音 | 完全解決 |

8 小節段落 = 2 個樂句：`half` → `authentic`。
12 小節段落 = 3 個樂句：`half` → `deceptive` → `authentic`。

**實作：**

```python
CADENCE_PLANS = {
    2: ["half", "authentic"],
    3: ["half", "deceptive", "authentic"],
    4: ["half", "imperfect", "deceptive", "authentic"],
}

def plan_phrases(section_name: str, bars: int, dance_type: str,
                 rng: random.Random) -> list[Phrase]:
    phrase_len = 8 if dance_type == "vals" else 4
    n = max(1, bars // phrase_len)
    plan = CADENCE_PLANS.get(n) or _extend_plan(n)
    # A_prime 的第 3 句可升級為 deceptive → 增加再現的戲劇性
    ...
```

#### 2.3 和聲往回填

```python
def fill_phrase_harmony(phrase: Phrase, section: Section,
                        progression_template: list[str],
                        rng: random.Random) -> list[ChordSlot]:
    """
    1. 先鎖定樂句最後 1–2 小節的終止和弦（依 phrase.cadence）
    2. 剩餘小節從 progression_template 取用，且必須「走得到」終止和弦
    3. 和聲節奏：句首慢（2 小節/和弦），接近終止加快（1 小節/和弦，
       最後一小節可 2 個和弦，如 V7 → i）
    """
```

**終止和弦對照表：**

```python
CADENCE_CHORDS = {
    "half":       {"minor": ["V7"],           "major": ["V7"]},
    "imperfect":  {"minor": ["V7", "i"],      "major": ["V7", "I"]},
    "deceptive":  {"minor": ["V7", "VI"],     "major": ["V7", "vi"]},
    "authentic":  {"minor": ["V7b9", "i"],    "major": ["V7", "I"]},
    "open":       {"minor": ["iv"],           "major": ["IV"]},
}
```

#### 2.4 和聲節奏成為變數

移除固定的 `bars_per_chord`。改為：

```python
def harmonic_rhythm_for_bar(local_bar: int, phrase_bars: int) -> int:
    """回傳這一小節要放幾個和弦。"""
    if local_bar >= phrase_bars - 1:
        return 2   # 終止小節：V7 → i
    if local_bar >= phrase_bars - 2:
        return 1   # 準備終止
    return 1 if local_bar % 2 == 1 else 0  # 0 = 延用上一和弦
```

#### 2.5 曲式模板改為黃金時代格式

```python
FORMS = {
    "golden_age_standard": {   # ← 新的預設
        "sections": [
            ("intro", 4), ("A", 16), ("B", 16),
            ("A", 16), ("variacion", 16), ("coda", 6),
        ],
    },
    "golden_age_short": {
        "sections": [("intro", 4), ("A", 16), ("B", 16), ("A_prime", 16), ("coda", 4)],
    },
    "aaba": {
        "sections": [("intro", 4), ("A", 16), ("A", 16), ("B", 16), ("A_prime", 16), ("coda", 4)],
    },
    "abab_vocal": {   # 含 estribillo（人聲段：密度降低、旋律簡化）
        "sections": [("intro", 4), ("A", 16), ("B", 16),
                     ("estribillo", 16), ("A_prime", 16), ("coda", 6)],
    },
}
```

`intro_aa_coda`（12 小節 A 段）**移除**——它是造成和聲斷裂的直接原因。

#### DoD

- [ ] `SECTION_NO_CADENCE` 與 `PHRASE_NO_CADENCE` 違規歸零
- [ ] `HARMONIC_RHYTHM_ORPHAN` 違規歸零
- [ ] 生成長度來到 2.5–3 分鐘（74 小節 @ 64 BPM 2/4 ≈ 2:19；`golden_age_standard` 應約 2:20–3:00）
- [ ] 聽感：每 4 小節聽得出「一句話」；每 16 小節聽得出「一段話說完了」

#### 不要做的事

- 不要在 M2 動旋律生成。旋律仍用現有的 `_phrase_contour`，只是接上新的樂句邊界。
- `variacion` 段在 M2 先當成 `A_prime` 處理，M8 才實作真正的 variación。

---

### M4 — 旋律三層重寫（**最重要的一步**）

**層級：** Skeleton / melody
**依賴：** M1、M2、M3
**預估：** 大

#### 動機

現行模型是 contour-first → snap to harmony：先畫抽象曲線，再貪心吸附到最近的和弦音。這保證「不會錯音」，但同時保證「不會有意義」。M4 改成 **structural-first → connect → decorate**。

#### 檔案

```
backend/app/engine/melody/
├── __init__.py
├── structural.py    # Pass 1：結構音
├── connect.py       # Pass 2：連接
├── decorate.py      # Pass 3：裝飾（yeites）
├── rhythm_cell.py   # 節奏動機（與音高動機分離）
└── nct.py           # 非和弦音的分類定義
```

`skeleton.py` 中以下函式**全部移除**：`_phrase_contour`、`_step_toward`、`_fit_pitches_to_harmony`、`_expand_pitches_to_count`、`_roll_contour_steps`。

#### 4.1 Pass 1 — 結構音（`structural.py`）

一個樂句先決定 2–4 個**目標音**，其餘一切都是通往目標的路徑。

```python
@dataclass
class StructuralNote:
    pitch: int
    bar: int            # 相對樂句起點
    beat: float         # 必須落在強拍（0.0 或 beats_per_bar/2）
    is_goal: bool       # 樂句的最終目標音
    chord_degree: int   # 1/3/5/7 — 在該和弦中的位置

def plan_structural_line(phrase: Phrase, chords: list[ChordSlot],
                         section: Section, prev_end: int | None,
                         rng: random.Random) -> list[StructuralNote]:
    """
    規則：
    1. 目標音由 phrase.cadence 決定：
       - authentic → 主音（chord_degree=1）
       - imperfect → 主和弦的 3 音或 5 音
       - half      → 屬和弦的 3 音（導音）或根音
       - deceptive → VI 的 3 音
    2. 樂句起音：
       - 若 prev_end 存在，起音與它相距 ≤5 半音（樂句間連貫）
       - 第一句可自由選 i 和弦音
    3. 中間 1–2 個結構音：形成一條可辨識的骨幹線
       骨幹形狀從以下抽樣（不是每次都下行）：
         "descent"   5→4→3→2→1  （探戈最常見）
         "arch"      1→3→5→3→1
         "ascent"    1→3→5      （用於 setup，需要後續 payoff）
         "plateau"   5→5→4→3    （同音反覆 + 遲滯下行，declamación）
         "leap_fill" 1→8ve→5→3→1（大跳開句 + 級進回填）
    4. 每個結構音必須是**該小節和弦**的和弦音
    """
```

**關鍵：`plateau` 與 `leap_fill` 兩種形狀必須存在。** 前者提供同音反覆（目前被程式碼消滅），後者提供大跳（目前實測 ≥5 半音只佔 1.7%）。

抽樣權重（tango）：

```python
CONTOUR_WEIGHTS = {
    "tango":   {"descent": 0.32, "arch": 0.20, "plateau": 0.20,
                "leap_fill": 0.16, "ascent": 0.12},
    "vals":    {"arch": 0.34, "ascent": 0.26, "descent": 0.24,
                "leap_fill": 0.12, "plateau": 0.04},
    "milonga": {"plateau": 0.34, "descent": 0.26, "arch": 0.20,
                "leap_fill": 0.12, "ascent": 0.08},
}
```

#### 4.2 節奏動機與音高動機分離（`rhythm_cell.py`）

```python
@dataclass
class RhythmCell:
    id: str
    onsets: list[float]        # 相對小節起點的拍位
    durations: list[float]
    anacrusis: float           # 弱起佔前一小節的拍數
    accent_pattern: list[bool] # 哪些音要重音

@dataclass
class PitchCell:
    id: str
    intervals: list[int]       # 相對第一個音的半音數（不是相鄰步進）
    contour_name: str
```

一首曲子 roll 出：**2–3 個 RhythmCell + 2–3 個 PitchCell**，兩者可以自由配對。這讓「同節奏換音高＝模進」與「同音高換節奏＝變奏」成為可能（M6 會用到）。

**弱起必須成為系統。** tango 的 RhythmCell 抽樣中，`anacrusis > 0` 的比例應 ≥ 0.5：

```python
TANGO_RHYTHM_CELLS = [
    RhythmCell("upbeat_3",   onsets=[0.0, 0.5, 1.0], durations=[0.5, 0.5, 1.0], anacrusis=0.5, ...),
    RhythmCell("declaim",    onsets=[0.0, 0.5, 1.0, 1.5], durations=[0.5]*4,   anacrusis=1.0, ...),
    RhythmCell("long_short", onsets=[0.0, 1.5],      durations=[1.5, 0.5],     anacrusis=0.0, ...),
    RhythmCell("syncopa",    onsets=[0.0, 0.75, 1.5],durations=[0.75,0.75,0.5],anacrusis=0.5, ...),
    RhythmCell("held",       onsets=[0.0],           durations=[2.0],          anacrusis=0.5, ...),
    RhythmCell("332",        onsets=[0.0, 0.75, 1.5],durations=[0.75,0.75,0.5],anacrusis=0.0, ...),
]
```

`held`（整小節長音）與 `long_short` 必須存在——它們提供目前完全缺席的呼吸感。

#### 4.3 Pass 2 — 連接（`connect.py`）

在結構音之間填音，但**每個填入的音都必須有分類**。

```python
# nct.py
class NCT(str, Enum):
    CHORD_TONE   = "chord_tone"
    PASSING      = "passing"        # 兩個和弦音之間、方向一致、級進
    NEIGHBOR     = "neighbor"       # 離開再回到同一個音
    APPOGGIATURA = "appoggiatura"   # 落在強拍、級進解決
    SUSPENSION   = "suspension"     # 前一和弦的音延續、級進下行解決
    ANTICIPATION = "anticipation"   # 提前唱出下一和弦的音
    ESCAPE       = "escape"         # 級進離開、跳進回來
    CHROMATIC    = "chromatic"      # 半音經過
```

```python
def connect(a: StructuralNote, b: StructuralNote,
            chord_a: ChordSlot, chord_b: ChordSlot,
            n_slots: int, rng: random.Random) -> list[MelodyNote]:
    """
    依 a→b 的距離與可用時值格數，選擇連接策略：
    - 距離 1–2 半音、1 格 → 直接接（或加 neighbor）
    - 距離 3–5 半音、2–3 格 → passing（含可能的 chromatic passing）
    - 距離 ≥7 半音、≥3 格 → 琶音上行 或 大跳 + 級進回填
    - 距離 0（同音）→ 保留同音反覆（declamación），或加 neighbor 後回
    每個產生的音都帶 nct 標籤。
    """
```

**硬約束（連接階段必須遵守）：**

1. 跳進 ≥5 半音之後，下一個音必須反方向級進（除非是琶音序列）
2. 一個樂句內不得出現兩次以上 ≥7 半音的跳進
3. 半音經過音只能出現在下行、且解決到和弦音
4. 強拍上的非和弦音只能是 appoggiatura 或 suspension（必須有解決）

#### 4.4 Pass 3 — 裝飾（`decorate.py`）

只在 **render 層**執行（因為裝飾密度是樂團風格差異的一部分），但生成的音仍要帶 `nct` 標籤。

實作以下 yeites（對應知識庫文件 §3.2）：

| 裝飾 | 實作 | 使用時機 |
|---|---|---|
| Apoyatura（倚音） | 目標音前偷 15–30% 時值，上或下方二度 | 樂句末長音、climax |
| Mordente（碎音） | 主音→鄰音→主音，總長 ≤ 主音 30% | 長音的中段 |
| Cromatismo | 兩個旋律音之間插半音階 | 級進下行 ≥3 半音時 |
| Arrastre | 目標音前 1–2 個極短的下方半音，velocity 遞增 | 重拍前、Pugliese 風格 |
| Variación | 把一個四分音符旋律改寫成 4 個十六分音符（琶音或音階） | variación 段、A_prime |
| Mugre | 同時彈相距小二度的兩個音 | 極高張力點，機率 < 5%，僅 dramatic 性格 |

裝飾機率由 `PERSONALITY_MIX[...]["decoration"]` × 張力曲線調節。

#### 4.5 休止必須被明確規劃

```python
def plan_rests(phrase: Phrase, rng: random.Random) -> set[int]:
    """
    回傳樂句內「旋律留白」的小節。
    規則：
    - 每個 4 小節樂句至少 1 個 ≥1 拍的休止
    - 休止優先放在樂句的第 2 小節末或第 4 小節（回答之後的呼吸）
    - 休止期間左手繼續 → 這是探戈的 call-and-response 基礎
    - Di Sarli 風格（pause_frequency=high）休止更多
    """
```

#### 4.6 密度參數必須真的生效

`DENSITY_NOTES_PER_BAR` 應控制 **Pass 2 的連接密度**（每兩個結構音之間填幾個音），而不是事後截斷。實測後每小節音數必須落在目標值 ±25% 內。

#### DoD

- [ ] `LEAP_NOT_RECOVERED`、`MELODY_NO_LONG_NOTE`、`MELODY_NO_REST`、`DENSITY_MISMATCH` 違規歸零
- [ ] `interval_hist` KL < 0.25（含 ≥5 半音跳進佔比 12–20%）
- [ ] `duration_hist` KL < 0.25（含 half + long 佔比 ≥ 20%）
- [ ] `repeated_note_ratio` 落在 0.10–0.20
- [ ] `rest_ratio` 落在 0.14–0.24
- [ ] 每個 MelodyNote 都帶 `nct` 與 `structural_weight` 欄位
- [ ] 聽感：旋律「唱得出來」；有明確的呼吸點；能哼

#### 不要做的事

- 不要為了通過統計測試而加隨機擾動。統計必須是音樂邏輯的**副產品**。

---

### M5 — 功能和聲語法

**層級：** Skeleton / harmony
**依賴：** M1、M2
**預估：** 中

#### 動機

取代「3 個固定進行模板」的做法。用加權的功能語法生成，讓和聲既有邏輯又有變化。

#### 檔案

`backend/app/engine/harmony/grammar.py`

#### 5.1 功能區與轉移機率

```python
# 功能區之間的轉移（不是和弦之間）
FUNCTION_TRANSITIONS = {
    "tonic":       {"subdominant": 0.50, "dominant": 0.28, "tonic": 0.12, "colour": 0.10},
    "subdominant": {"dominant": 0.62, "subdominant": 0.20, "colour": 0.12, "tonic": 0.06},
    "dominant":    {"tonic": 0.72, "dominant": 0.16, "colour": 0.08, "subdominant": 0.04},
    "colour":      {"dominant": 0.48, "subdominant": 0.30, "tonic": 0.22},
}

# 功能區內部的和弦選擇（依 style profile 的 dissonance_level 調整權重）
CHORD_CHOICE = {
    "tonic":       {"i": 0.55, "i6": 0.12, "iM7": 0.08, "i7": 0.08, "III": 0.12, "I": 0.05},
    "subdominant": {"iv": 0.42, "iiø7": 0.18, "VI": 0.14, "bVII": 0.10,
                    "iv6": 0.08, "bII": 0.05, "IV": 0.03},
    "dominant":    {"V7": 0.44, "V7b9": 0.26, "V": 0.12, "vii°7": 0.10, "subV7": 0.05, "Ger+6": 0.03},
    "colour":      {"V7/iv": 0.28, "V7/V": 0.26, "V7/VI": 0.20, "V7/III": 0.14, "III+": 0.12},
}
```

#### 5.2 Style profile 調節

```json
"harmonic_tendencies": {
  "chromatic_density": 0.15,
  "seventh_frequency": 0.4,
  "secondary_dominant_rate": 0.2,
  "borrowed_chords_frequency": "medium",
  "dissonance_level": "low"
}
```

- D'Arienzo：`chromatic_density` 低、`seventh_frequency` 低 → 簡單有力
- Pugliese：`chromatic_density` 高、`dissonance_level` high → 繞、有張力
- Di Sarli：中等，但 `borrowed_chords_frequency` 偏高（IVm 是他的招牌）

#### 5.3 半音低音線（特別處理）

這是探戈最標誌性的和聲手法之一，需要專門的生成器：

```python
def chromatic_bass_run(start_chord: str, bars: int, mode: str) -> list[str]:
    """
    生成半音下行的低音線，維持同一和聲功能。
    例：i → iM7 → i7 → i6   （A → G# → G → F#）
        iv → iv/b3 → V7/...
    在 A/A_prime 段落的第 2 樂句最常見。
    """
```

觸發機率由 `chromatic_density` 控制，每 16 小節段落最多出現一次。

#### 5.4 約束

語法生成後必須通過：

1. 樂句末必須符合 M2 的終止式規則（語法是生成中段，終止是硬規則）
2. 次屬和弦後面必須跟它的目標和弦（`V7/iv` → `iv`）
3. `bII` 後面必須是 `V7` 或 `i`（拿坡里的功能是導向屬）
4. 增六和弦後面必須是 `V7`
5. 同一和弦不得連續出現超過 4 小節（除非是刻意的 pedal）

實作方式：生成 → 檢查 → 失敗則重採樣（最多 20 次）→ 仍失敗則退回固定模板。

#### DoD

- [ ] `chord_transition` 矩陣的熵顯著高於 M4 之後的 baseline
- [ ] 100 個 seed 中，次屬和弦出現率 15–30%，借用和弦出現率 10–25%
- [ ] `CHORD_SPELLING_INVALID` 仍為零
- [ ] 聽感：Pugliese 明顯比 D'Arienzo「繞」；同一風格多次生成和聲不重複

---

### M6 — 動機發展手法

**層級：** Skeleton / melody
**依賴：** M4
**預估：** 中

#### 動機

目前只有一個 0–3 的「密度發展軸」。真正的動機發展有明確的手法清單，而且**手法本身應該是可教學的內容**。

#### 檔案

`backend/app/engine/melody/development.py`

#### 6.1 手法清單

```python
class DevelopmentTechnique(str, Enum):
    LITERAL       = "literal"        # 原樣重現
    SEQUENCE      = "sequence"       # 模進：同 RhythmCell + PitchCell 平移 n 度
    INVERSION     = "inversion"      # 倒影：音程反向
    AUGMENTATION  = "augmentation"   # 擴增：時值 ×2
    DIMINUTION    = "diminution"     # 縮減：時值 ÷2
    FRAGMENTATION = "fragmentation"  # 片段化：只取動機前半，反覆
    EXTENSION     = "extension"      # 延伸：動機末尾加尾巴
    ORNAMENTATION = "ornamentation"  # 加花：同骨架、更多裝飾音
    REHARMONIZATION = "reharmonization"  # 同旋律換和聲
    RHYTHM_SWAP   = "rhythm_swap"    # 同 PitchCell 換 RhythmCell
    PITCH_SWAP    = "pitch_swap"     # 同 RhythmCell 換 PitchCell
```

#### 6.2 段落層的手法分配

```python
SECTION_TECHNIQUES = {
    "A":         [LITERAL, SEQUENCE, LITERAL, EXTENSION],
    "B":         [PITCH_SWAP, SEQUENCE, FRAGMENTATION, EXTENSION],
    "A_prime":   [ORNAMENTATION, SEQUENCE, REHARMONIZATION, ORNAMENTATION],
    "variacion": [DIMINUTION, DIMINUTION, FRAGMENTATION, DIMINUTION],
    "coda":      [FRAGMENTATION, AUGMENTATION],
    "bridge":    [FRAGMENTATION, RHYTHM_SWAP],
}
```

每個樂句記錄它用了什麼手法，寫入 IR（M9 會用來做教學顯示）。

#### 6.3 Setup / Payoff

保留現有的 `_plan_motif_setup_payoff` 概念，但改為明確的：

```python
@dataclass
class MotifPlan:
    cell_id: str
    first_appearance: int      # bar
    developments: list[tuple[int, DevelopmentTechnique]]
    payoff_bar: int            # 通常對齊 climax
    payoff_technique: DevelopmentTechnique  # 通常 AUGMENTATION 或 ORNAMENTATION
```

#### DoD

- [ ] 每個樂句的 IR 帶 `motif_id` + `technique`
- [ ] 同一 seed 的 A 段與 A_prime 段，PitchCell 的 intervals 相似度 > 0.7（是同一個主題）
- [ ] B 段與 A 段的 PitchCell 相似度 < 0.4（是對比主題）
- [ ] 聽感：能哼出核心句；A_prime 聽得出「同一句話講第二次，更豐富」

---

### M7 — Archetype 多樣性

**層級：** Skeleton 計劃層
**依賴：** M2、M4、M5
**預估：** 小

#### 動機

解決「每次生成都很像」。**多樣性要在計劃層抽樣，不是在音符層加隨機。**

#### 檔案

`backend/app/engine/archetype.py`

```python
@dataclass
class PieceArchetype:
    id: str
    form_id: str
    total_bars_range: tuple[int, int]
    modulation_plan: str        # "none" | "relative" | "parallel" | "dominant" | "chain"
    tension_shape: str          # "single_peak" | "double_peak" | "front_loaded"
                                # | "staircase" | "sudden_collapse" | "late_bloom"
    motif_style: str            # "rhythmic" | "melodic" | "harmonic"
    texture_plan: str           # 誰在什麼時候扛旋律
    density_curve: str
    repeat_ratio: float         # 重複 vs 變奏的比例

ARCHETYPES = [
    PieceArchetype("classic_dance",  form_id="golden_age_standard",
                   modulation_plan="relative", tension_shape="staircase",
                   motif_style="rhythmic", ...),
    PieceArchetype("lyrical_song",   form_id="abab_vocal",
                   modulation_plan="parallel", tension_shape="late_bloom",
                   motif_style="melodic", ...),
    PieceArchetype("dramatic_arc",   form_id="golden_age_standard",
                   modulation_plan="chain", tension_shape="double_peak",
                   motif_style="harmonic", ...),
    PieceArchetype("compact_milonga", form_id="golden_age_short",
                   modulation_plan="none", tension_shape="front_loaded", ...),
    PieceArchetype("dark_meditation", form_id="aaba",
                   modulation_plan="parallel", tension_shape="sudden_collapse", ...),
]
```

#### 7.1 張力曲線形狀

取代目前的單一插值。每種形狀是一個函式 `(bar, total_bars) -> float`：

```python
TENSION_SHAPES = {
    "single_peak":     lambda t: math.sin(t * math.pi) ** 0.7,
    "double_peak":     lambda t: max(math.sin(t*2*math.pi)**2 * 0.8, ...),
    "staircase":       lambda t: math.floor(t * 4) / 4 + 0.1,
    "front_loaded":    lambda t: (1 - t) ** 0.6 * 0.8 + 0.2,
    "sudden_collapse": lambda t: 1.0 if t < 0.7 else 0.2,
    "late_bloom":      lambda t: t ** 2.2,
}
```

#### 7.2 API 擴充

```python
class SkeletonRequest(BaseModel):
    ...
    archetype_id: str | None = "random"
```

前端加一個「曲風原型」選單（含「隨機」選項與雙語說明），這對教學也有價值。

#### DoD

- [ ] 100 個 seed 中出現 ≥5 種不同的總小節數
- [ ] 張力曲線的形狀分佈涵蓋所有 6 種
- [ ] 聽感：連續聽 5 首，founder 不會覺得「同一首的不同配音」

---

### M8 — 配器角色與 variación

**層級：** Render / arrange
**依賴：** M4、M6
**預估：** 大

#### 動機

目前 6 個樂團的差異只有「LH pattern + 混音音量 + decoration 機率」。bandoneón 永遠是長 pad、弦樂永遠是長音。**orquesta típica 的識別特徵是「誰在什麼時候做什麼」，不是「用什麼音色」。**

#### 檔案

`backend/app/engine/arrange/roles.py`

#### 8.1 角色模型

```python
class Role(str, Enum):
    LEAD          = "lead"           # 主旋律
    COUNTERMELODY = "countermelody"  # 對唱旋律（contracanto）
    MARCATO       = "marcato"        # 節奏骨幹
    PAD           = "pad"            # 和聲背景
    BASS          = "bass"
    FILL          = "fill"           # 樂句間的填充樂句（bordoneo）
    VARIACION     = "variacion"      # 十六分音符炫技

@dataclass
class SectionArrangement:
    section: str
    assignments: dict[str, Role]   # instrument → role
```

#### 8.2 各樂團的角色分配表

寫入 style profile 的新欄位 `arrangement_plan`：

```json
"arrangement_plan": {
  "intro":     { "piano": "marcato", "bandoneon": "lead",  "violin": "pad",  "cello": "bass" },
  "A":         { "piano": "marcato", "bandoneon": "lead",  "violin": "countermelody", "cello": "bass" },
  "B":         { "piano": "marcato", "bandoneon": "pad",   "violin": "lead", "cello": "bass" },
  "A_prime":   { "piano": "lead",    "bandoneon": "marcato","violin": "countermelody", "cello": "bass" },
  "variacion": { "piano": "marcato", "bandoneon": "variacion", "violin": "pad", "cello": "bass" },
  "coda":      { "piano": "marcato", "bandoneon": "lead",  "violin": "lead", "cello": "bass" }
}
```

**旋律交接**是關鍵：同一條旋律線在不同段落由不同樂器演奏。這需要 render 層能把 skeleton 的 melody 分配給任意樂器（目前寫死 `piano_rh`）。

#### 8.3 對唱旋律（contracanto）

```python
def generate_countermelody(lead: list[MelodyNote], chords: list[ChordSlot],
                           rng: random.Random) -> list[MelodyNote]:
    """
    規則：
    - 在 lead 的休止處進入（call-and-response）
    - 與 lead 同時發聲時，維持三度或六度平行，或反向進行
    - 禁止與 lead 平行五度／八度
    - 音域低於 lead 一個八度左右
    """
```

#### 8.4 Variación 段

黃金時代錄音幾乎必有的橋段：最後一段由 bandoneón 演奏連續十六分音符。

```python
def generate_variacion(motif: PitchCell, chords: list[ChordSlot],
                       rng: random.Random) -> list[MelodyNote]:
    """
    - 每拍 4 個十六分音符，連續不斷
    - 音高走和弦琶音 + 半音經過音
    - 大方向仍跟隨原動機的骨幹音
    - 音域寬（可跨 2–3 個八度）
    """
```

**這一段做出來，「像不像」會立刻上一個台階。**

#### 8.5 播放層音色（前端）

`frontend/src/audio/pianoPlayer.ts` 目前 bandoneón / violin / cello 都是 `Tone.PolySynth`。

- **優先：找 bandoneón sample。** 沒有 bandoneón 音色就沒有探戈——這件事對「像不像」的影響可能大於三個 M-task 加起來。
- 弦樂加 portamento（`Tone.Sampler` + 手動 pitch glide，或用 `PolySynth` 的 `portamento` 參數）。滑音是 Di Sarli / Pugliese 的招牌。
- 檔案改名：`pianoPlayer.ts` → `ensemblePlayer.ts`

#### DoD

- [ ] 切換樂團時，聽得出「誰在演奏旋律」不同
- [ ] variación 段可辨識
- [ ] contracanto 與 lead 沒有平行五度／八度
- [ ] bandoneón 用真實 sample

---

### M9 — 教學 IR 與逐層剝開 UI

**層級：** 全棧
**依賴：** M4、M6、M8
**預估：** 中

#### 動機

**這是規則引擎相對於 AI 音訊模型唯一且巨大的優勢，應該當成產品核心而不是附加功能。**

#### 9.1 完整的 NoteEvent IR

```python
@dataclass
class MelodyNote:
    # 基本
    pitch: int
    start_beat: float
    duration_beats: float
    velocity: int
    track: str

    # 音樂意義（M9 的核心）
    nct: NCT                        # chord_tone / passing / appoggiatura / ...
    structural_weight: str          # "structural" | "connective" | "ornamental"
    resolves_to: int | None         # 非和弦音解決到哪個音高
    chord_symbol: str               # 這一刻的和弦
    chord_function: str             # tonic / subdominant / dominant / colour
    motif_id: str | None
    development_technique: str | None
    phrase_index: int
    phrase_role: str                # question / answer
    cadence_role: str | None        # 若是終止音，是哪種終止
    role: Role                      # lead / countermelody / fill / ...
    layer: int                      # 見 9.2
```

**這同時解決教學需求：拆解成份不需要事後分析，生成時就已經標好了。**

#### 9.2 逐層剝開

```python
LAYERS = {
    0: "harmony_only",      # 只有和弦（block chords，每小節一次）
    1: "structural_melody", # + 骨幹旋律（只有 structural_weight == "structural"）
    2: "connected_melody",  # + 連接音
    3: "decorated_melody",  # + 裝飾音
    4: "left_hand",         # + 左手節奏
    5: "full_ensemble",     # + 配器
}
```

API：`POST /api/render` 加參數 `layer: int = 5`，回傳只含該層以下的音符。

前端加一個 layer slider，可以獨立播放每一層。**這個 UI 幾乎是免費的**——IR 一做完就只是過濾。

#### 9.3 解釋文字

每個和弦與每個非和弦音都能產生一句雙語解釋：

```python
def explain_chord(slot: ChordSlot, ctx: Context) -> dict[str, str]:
    """
    例：
    zh: "V7/iv（A7）是 iv 的次屬和弦，它把 D 小三和弦暫時當成臨時主音，
         讓下一小節的 iv 聽起來更有到達感。"
    en: "V7/iv (A7) is the secondary dominant of iv, ..."
    """

def explain_note(note: MelodyNote, ctx: Context) -> dict[str, str]:
    """
    例：
    zh: "這個 F 是倚音——它落在強拍上、不屬於當下的 E7 和弦，
         然後級進下行解決到 E。這是探戈最常用的表情手法。"
    """
```

前端：piano-roll 上點任一音符 → 顯示解釋。

#### 9.4 MusicXML 標註

`export_formats.py` 加上：

- `<harmony>` 和弦記號（M1 已做）
- 非和弦音加 `<notations><technical>` 或 lyrics 標註 nct 類型（可選開關）
- 樂句邊界用 `<barline>` 或 phrase mark

#### DoD

- [ ] layer 0–5 都能獨立播放且音樂上合理
- [ ] 點擊任一音符能看到雙語解釋
- [ ] MusicXML 在 MuseScore 開啟時能看到和弦記號與樂句線

---

## 3. 建議執行順序與時程

| 順序 | M-task | 理由 |
|---|---|---|
| 1 | **M3** | 沒有測量工具，後面所有改動都無法驗證 |
| 2 | **M1** | 修 bug，範圍小，立即消除「違和感」 |
| 3 | **M2** | 修結構性 bug，且是 M4 的前置 |
| 4 | **M4** | 影響最大的單一改動 |
| 5 | **M5** | 和聲詞彙上線，多樣性第一波 |
| 6 | **M6** | 動機發展，讓長曲有邏輯 |
| 7 | **M7** | 多樣性第二波（宏觀） |
| 8 | **M8** | 配器 + 音色，「像不像」的最後一哩 |
| 9 | **M9** | 教學價值兌現 |

**每個 M-task 之後的固定流程：**

```bash
pytest tests/musicality/ -v
python scripts/musicality-report.py --dance tango --seeds 100
python scripts/musicality-report.py --dance vals --seeds 50
python scripts/musicality-report.py --dance milonga --seeds 50
# 更新 docs/musicality-baseline.md
# 生成 5 個 seed 的 MIDI 給 founder 聽
git commit
```

---

## 4. 給 Cursor 的實作提醒

1. **不要為了讓測試通過而加隨機擾動。** 統計指標必須是音樂邏輯的副產品。如果為了讓 `leap_ratio` 達標而隨機插入跳進，那只是把一種難聽換成另一種。

2. **每個 M-task 都要保持 seed 可重現。** 所有隨機都經過傳入的 `random.Random(seed)`，不得使用全域 `random`。

3. **不要在同一個 PR 裡改 API 契約與音樂邏輯。** 若某個 M-task 需要改 `/api/skeleton` 的回傳結構，先開一個獨立的 PR 改契約 + 前端，再改邏輯。

4. **`skeleton.py` 目前 2668 行，M4 之後應該 < 400 行。** 若做完 M4 它還很大，代表拆分沒做徹底。

5. **音樂術語一律用探戈的原文**（marcato、síncopa、arrastre、yeites、variación、contracanto、bordoneo、estribillo），不要意譯成通用音樂術語。這對教學網站的可信度很重要。

6. **雙語文案**：所有面向使用者的字串都要有 `zh`（繁體中文）與 `en` 兩版，走既有的 i18n 機制。

7. **Style profile 的 schema 會擴充**（M5 加 `harmonic_tendencies` 欄位、M8 加 `arrangement_plan`）。建議加一個 `backend/app/schemas/style_profile.json` 做 JSON Schema 驗證，並在 `data_loader.py` 載入時檢查。

8. **不要刪除既有的 E-task 成果。** E2（A′ 闡述）、E9（結構錨點）、E11（motivic cells）的概念都要保留，只是搬到新架構的對應位置：E2 → M6 的 `A_prime` 手法表；E9 → M7 的 tension shape；E11 → M4 的 PitchCell / RhythmCell。

---

## 5. 附錄：可以參考的既有專案內文件

| 文件 | 用途 |
|---|---|
| `docs/research/Tango_music_synthesis.md` | 引擎分層規格的原始研究 |
| `docs/product/PROJECT_PLAN.md` §3b | E-task 對照，M-task 完成後要更新狀態 |
| founder 的「阿根廷探戈鋼琴即興演奏完整指南」 | 和聲詞彙、yeites、曲式的權威來源，M1/M4/M5 應以它為準 |
| `docs/research/milonga_story1.md` / `milonga_story2.md` | milonga 的風格背景 |
