# TangoAtelier frontend

Vite + React + TypeScript. Local API calls are proxied to `http://127.0.0.1:8000`.

```bash
cd frontend
pnpm install
pnpm dev
```

Set `VITE_API_BASE` only when the API is on a different origin (e.g. separate Zeabur service URL).
