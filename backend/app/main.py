from __future__ import annotations

import base64
import os
from pathlib import Path
from typing import Any, Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app.data_loader import list_orchestras, load_orchestra
from app.engine import SIMPLE_PROFILE, build_skeleton, generate_piece, render_skeleton
from app.engine.catalog import atelier_options

STATIC_DIR = Path(os.getenv("STATIC_DIR", "")).expanduser()


def _cors_origins() -> list[str]:
    raw = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173,https://tangoatelier.zeabur.app",
    )
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


app = FastAPI(title="TangoAtelier API", version="0.3.0")

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
    dance_type: Literal["tango", "milonga", "vals"] = "tango"


MelodyLevel = Literal["low", "medium", "high"]


class SkeletonRequest(BaseModel):
    dance_type: Literal["tango", "milonga", "vals"] = "tango"
    key: str | None = None
    progression_id: str | None = "random"
    form_id: str | None = "intro_aa_coda"
    melody_density: MelodyLevel = "medium"
    melody_variation: MelodyLevel = "medium"
    seed: int | None = Field(default=None, ge=1, le=2_147_483_647)


class RenderInstruments(BaseModel):
    piano: bool | None = None
    bandoneon: bool | None = None
    strings: bool | None = None


class RenderRequest(BaseModel):
    skeleton: dict[str, Any]
    orchestra_id: str = "simple"
    seed: int | None = Field(default=None, ge=1, le=2_147_483_647)
    instruments: RenderInstruments | None = None


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


@app.get("/api/atelier/options")
def get_atelier_options() -> dict:
    opts = atelier_options()
    # Attach real orchestras as render styles
    opts["render_styles"] = [{"id": "simple", "personality_type": "neutral"}] + [
        {
            "id": o["id"],
            "personality_type": o["personality_type"],
            "personality_emoji": o["personality_emoji"],
            "name": o["name"],
        }
        for o in list_orchestras()
    ]
    return opts


@app.post("/api/skeleton")
def post_skeleton(body: SkeletonRequest) -> dict:
    try:
        return build_skeleton(
            dance_type=body.dance_type,
            key=body.key,
            progression_id=body.progression_id,
            form_id=body.form_id,
            melody_density=body.melody_density,
            melody_variation=body.melody_variation,
            seed=body.seed,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Skeleton failed: {exc}") from exc


@app.post("/api/render")
def post_render(body: RenderRequest) -> dict:
    if body.orchestra_id == "simple":
        profile = SIMPLE_PROFILE
    else:
        try:
            profile = load_orchestra(body.orchestra_id)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail="Orchestra not found") from exc
    try:
        inst = None
        if body.instruments is not None:
            inst = {
                k: v
                for k, v in body.instruments.model_dump().items()
                if v is not None
            }
        return render_skeleton(
            body.skeleton,
            profile,
            seed=body.seed,
            instruments=inst or None,
            include_midi=True,
            include_musicxml=False,
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Render failed: {exc}") from exc


@app.post("/api/generate")
def post_generate(body: GenerateRequest) -> dict:
    try:
        profile = load_orchestra(body.orchestra_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Orchestra not found") from exc
    try:
        return generate_piece(
            profile,
            seed=body.seed,
            include_midi=True,
            include_musicxml=False,
            dance_type=body.dance_type,
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Generation failed: {exc}") from exc


@app.get("/api/generate/{orchestra_id}/midi")
def download_midi(orchestra_id: str, seed: int | None = None) -> Response:
    try:
        profile = load_orchestra(orchestra_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Orchestra not found") from exc
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
