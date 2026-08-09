# TangoAtelier API

FastAPI backend for orchestra Style Profiles (Phase 0+) and later music generation.

## Local run

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
PYTHONPATH=. uvicorn app.main:app --reload --port 8000
```

- Health: `GET /health`
- Orchestras: `GET /api/orchestras`
- Detail: `GET /api/orchestras/{id}`
- OpenAPI: `/docs`

Style profiles live in `data/style_profiles/*.json`.
