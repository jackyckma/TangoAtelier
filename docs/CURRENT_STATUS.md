# Current status

**Last updated:** 2026-08-09

## Summary

**TangoAtelier** Phase 1 + UX：生成／播放嵌在樂團詳情頁（可對照介紹）；呈現每團 Style Profile 預設參數＋本次生成實際值。線上：https://tangoatelier.zeabur.app

## What works

- 樂團詳情頁：bio／聲音描述＋右側（桌面 sticky）生成器
- 風格參數面板（節奏、速度、articulation、和聲傾向等）
- `POST /api/generate`、MIDI／MusicXML、Salamander 播放
- `/generate/:id` 會 redirect 到詳情 `#listen`

## Known gaps

- 參數暫為說明用，尚未做成可調滑桿
- 聽感差異仍偏鋼琴單聲部；編制／音色待 Phase 3
- 更深的「樂團特徵」可用日後 data analysis 校正權重（非阻塞）
- Hint／Save／Share 仍在後續 Phase

## Next steps

1. 依 feedback 決定參數要不要變滑桿、以及編制音色優先度
2. Phase 2／3／4 排序
