---
status: active
maintained_by: ai-agents
created: 2026-08-09
last_updated: 2026-08-09
purpose: Which verification levels and tasks work in local Cursor vs Cloud Agents.
---

# Agent environment capability matrix

## Environments

| Environment | Used for | Secrets source |
|-------------|----------|----------------|
| Local Cursor | L2/L3 integration, full stack | `.env`（gitignored） |
| Cloud Agent | L0+L1 coding, docs | Cloud UI injection |
| Zeabur | L4 HTTP smoke（接好後） | Zeabur env vars |

## Staging / production URL

- **URL:** *pending — founder 接 Zeabur 後填入*
- **Deploy branch:** `main`
- **Smoke command:** *pending*（例如 `curl -sf "$URL/api/health"`）

## Verification commands

| Level | Command | Cloud-safe? |
|-------|---------|:-----------:|
| L0 | *Phase 0 後設定*（frontend lint/typecheck + backend ruff/check） | ✅ |
| L1 | *Phase 0 後設定*（vitest + pytest） | ✅ |
| L2 | 本機前後端 integration | ❌ local |
| L3 | `pnpm dev` + `uvicorn` 手動 | ❌ local |
| L4 | Zeabur URL smoke | ✅ |

## Local-only tasks

- 長時間聽感／音色主觀驗收（Phase 1+）
- MuseScore 匯入 MusicXML 手動檢查

## Optional services

| Service | Required for dev? | Stub available? |
|---------|:-----------------:|:---------------:|
| Zeabur | 否（本機可開發） | N/A |
| LLM APIs | 否（生成不用 LLM） | N/A |
| Object storage | Phase 5 前否 | 可先把 MusicXML 存 DB／磁碟 |
