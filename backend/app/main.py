from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app.data_loader import list_orchestras, load_orchestra
from app.engine import generate_piece

STATIC_DIR = Path(os.getenv("STATIC_DIR", "")).expanduser()


def _cors_origins() -> list[str]:
    raw = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173,https://tangoatelier.zeabur.app",
    )
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


app = FastAPI(title="TangoAtelier API", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class GenerateRequest(BaseModel):
    orchestra_id: str
    seed: int | None = Field(default=None, ge=1, le=2_147_483_647)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/orchestras")
def get_orchestras() -> list[dict]:
    return list_orchestras()


@app.get("/api/orchestras/{orchestra_id}")
def get_orchestra(orchestra_id: str) -> dict:
    try:
        return load_orchestra(orchestra_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Orchestra not found") from exc


@app.post("/api/generate")
def post_generate(body: GenerateRequest) -> dict:
    try:
        profile = load_orchestra(body.orchestra_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Orchestra not found") from exc
    try:
        return generate_piece(
            profile, seed=body.seed, include_midi=True, include_musicxml=False
        )
    except Exception as exc:  # noqa: BLE001 — surface as 500 with message
        raise HTTPException(status_code=500, detail=f"Generation failed: {exc}") from exc


@app.get("/api/generate/{orchestra_id}/midi")
def download_midi(orchestra_id: str, seed: int | None = None) -> Response:
    try:
        profile = load_orchestra(orchestra_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Orchestra not found") from exc
    import base64

    piece = generate_piece(profile, seed=seed, include_midi=True, include_musicxml=False)
    data = base64.b64decode(piece["midi_base64"])
    filename = f"tangoatelier-{orchestra_id}-{piece['seed']}.mid"
    return Response(
        content=data,
        media_type="audio/midi",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.get("/api/generate/{orchestra_id}/musicxml")
def download_musicxml(orchestra_id: str, seed: int | None = None) -> Response:
    try:
        profile = load_orchestra(orchestra_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Orchestra not found") from exc
    piece = generate_piece(
        profile, seed=seed, include_midi=False, include_musicxml=True
    )
    filename = f"tangoatelier-{orchestra_id}-{piece['seed']}.musicxml"
    return Response(
        content=piece["musicxml"],
        media_type="application/vnd.recordare.musicxml+xml",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.get("/api")
def api_root() -> dict[str, str]:
    return {
        "service": "TangoAtelier API",
        "docs": "/docs",
        "health": "/health",
    }


def _static_ready() -> bool:
    return STATIC_DIR.is_dir() and (STATIC_DIR / "index.html").is_file()


if _static_ready():
    assets = STATIC_DIR / "assets"
    if assets.is_dir():
        app.mount("/assets", StaticFiles(directory=assets), name="assets")

    @app.get("/")
    def spa_index() -> FileResponse:
        return FileResponse(STATIC_DIR / "index.html")

    @app.get("/{full_path:path}")
    def spa_fallback(full_path: str) -> FileResponse:
        reserved = ("api/", "docs", "redoc", "openapi.json", "health")
        if full_path == "api" or full_path.startswith(reserved):
            raise HTTPException(status_code=404, detail="Not found")
        candidate = STATIC_DIR / full_path
        if candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(STATIC_DIR / "index.html")
else:

    @app.get("/")
    def root() -> dict[str, str]:
        return {
            "service": "TangoAtelier API",
            "docs": "/docs",
            "health": "/health",
            "note": "STATIC_DIR not set — API only",
        }
