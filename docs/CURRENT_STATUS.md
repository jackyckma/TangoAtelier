# Current status

**Last updated:** 2026-08-09

## Summary

**TangoAtelier** Phase 0 骨架已落地。Zeabur 已接：project `6a78ae73e4a69d66638d7bd2`，service `service-6a78b36fe4a69d66638d7d59`，URL https://tangoatelier.zeabur.app。Save／Share 確認跟 Phase 5。下一步：**Phase 1** 規則引擎＋音色。

## What works

- Methodology scaffolding + project plan
- `GET /health`, `GET /api/orchestras`, `GET /api/orchestras/{id}`
- 6 profiles：D'Arienzo、Biagi、Troilo、Di Sarli、Canaro、Pugliese（雙語）
- Frontend browse + i18n（資料來自 API）
- `pnpm` build 通過
- Zeabur IDs／公開 URL 已記錄

## Known gaps

- 部署可能需前後端雙 service／路由調整（目前只記了一個 service id）
- CORS 目前只開本機
- 生成器按鈕尚為 Phase 1 placeholder
- Soundfont／規則引擎尚未實作

## Next steps

1. 確認 Zeabur 部署健康（首頁＋`/api` 或 `/health`）
2. 開始 **Phase 1**（規則引擎＋ MusicXML／MIDI＋ Tone.js soundfont）
