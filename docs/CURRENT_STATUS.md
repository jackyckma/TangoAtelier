# Current status

**Last updated:** 2026-08-09

## Summary

**TangoAtelier** Phase 1 已落地：規則引擎可依 Style Profile 生成原創鋼琴段落（note events + MIDI + MusicXML），前端生成器以 Tone.js Salamander 鋼琴播放。線上：https://tangoatelier.zeabur.app

## What works

- Phase 0 樂團瀏覽＋i18n＋Zeabur 單一 Docker service
- `POST /api/generate`、MIDI／MusicXML 下載
- `/generate/:id` 生成器：生成／播放／停止／下載
- D'Arienzo（marcato_en_cuatro）vs Di Sarli（pesante）等節奏型態已分流

## Known gaps

- Hint 視覺化尚未做（Phase 4）
- 曲式／長度／編制選項尚未做（Phase 2–3）
- Save／Share 在 Phase 5
- 旋律仍為骨架級，藝術完整度有限（符合教學優先）

## Next steps

1. Deploy 後聽感驗收（尤其 D'Arienzo vs Di Sarli）
2. Phase 2 或依優先度調整
