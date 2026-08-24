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
from app.engine.lab import build_lab_skeleton, extend_lab_skeleton, resolve_ensemble
from app.engine.lab_catalog import lab_options
from app.engine.generation_options import normalize_generation_options

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
    form_id: str | None = "golden_age_short"
    melody_density: MelodyLevel = "medium"
    melody_variation: MelodyLevel = "medium"
    seed: int | None = Field(default=None, ge=1, le=2_147_483_647)


class RenderInstruments(BaseModel):
    piano: bool | None = None
    guitar: bool | None = None
    bandoneon: bool | None = None
    strings: bool | None = None


class GenerationOptions(BaseModel):
    expectancy_gate: bool | None = None
    surface_reharm: str | None = None
    motivic_cells: str | None = None
    phrase_transform_aggressive: bool | None = None
    b_groove_contrast_run: bool | None = None
    yeites_intensity: str | None = None
    a_prime_elaboration: bool | None = None
    harmonic_grammar: str | None = None


class LabSkeletonRequest(BaseModel):
    dance_type: Literal["tango", "milonga", "vals"] = "tango"
    mode: str | None = "minor"
    progression_character: str | None = "diatonic"
    archetype_id: str | None = "segment_song"
    melody_density: MelodyLevel = "medium"
    melody_variation: MelodyLevel = "medium"
    intent_tags: list[str] | None = None
    generation_options: GenerationOptions | None = None
    seed: int | None = Field(default=None, ge=1, le=2_147_483_647)


class LabExtendRequest(LabSkeletonRequest):
    seed: int = Field(ge=1, le=2_147_483_647)


class LabRenderRequest(BaseModel):
    skeleton: dict[str, Any]
    layer: Literal["theme", "groove", "ensemble"] = "theme"
    ensemble_id: str | None = "solo_piano"
    style_id: str | None = "simple"
    seed: int | None = Field(default=None, ge=1, le=2_147_483_647)
    generation_options: GenerationOptions | None = None
    instruments: RenderInstruments | None = None


class RenderRequest(BaseModel):
    skeleton: dict[str, Any]
    orchestra_id: str = "simple"
    seed: int | None = Field(default=None, ge=1, le=2_147_483_647)
    instruments: RenderInstruments | None = None


def _gen_opts_dict(body_opts: GenerationOptions | None) -> dict[str, Any] | None:
    if body_opts is None:
        return None
    raw = {k: v for k, v in body_opts.model_dump().items() if v is not None}
    return normalize_generation_options(raw) if raw else None


def _instruments_dict(body: RenderInstruments | None) -> dict[str, bool] | None:
    if body is None:
        return None
    return {k: v for k, v in body.model_dump().items() if v is not None}


def _load_style_profile(style_id: str) -> dict:
    if style_id == "simple":
        return SIMPLE_PROFILE
    return load_orchestra(style_id)


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


@app.get("/api/lab/options")
def get_lab_options() -> dict:
    refs = [
        {
            "id": o["id"],
            "personality_type": o["personality_type"],
            "personality_emoji": o["personality_emoji"],
            "name": o["name"],
        }
        for o in list_orchestras()
    ]
    return lab_options(style_references=refs)


@app.post("/api/lab/skeleton")
def post_lab_skeleton(body: LabSkeletonRequest) -> dict:
    try:
        return build_lab_skeleton(
            dance_type=body.dance_type,
            mode=body.mode,
            progression_character=body.progression_character,
            archetype_id=body.archetype_id,
            melody_density=body.melody_density,
            melody_variation=body.melody_variation,
            intent_tags=body.intent_tags,
            generation_options=_gen_opts_dict(body.generation_options),
            seed=body.seed,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Lab skeleton failed: {exc}") from exc


@app.post("/api/lab/extend")
def post_lab_extend(body: LabExtendRequest) -> dict:
    try:
        return extend_lab_skeleton(
            seed=body.seed,
            dance_type=body.dance_type,
            mode=body.mode,
            progression_character=body.progression_character,
            melody_density=body.melody_density,
            melody_variation=body.melody_variation,
            intent_tags=body.intent_tags,
            generation_options=_gen_opts_dict(body.generation_options),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Lab extend failed: {exc}") from exc


@app.post("/api/lab/render")
def post_lab_render(body: LabRenderRequest) -> dict:
    skeleton = dict(body.skeleton)
    opts = _gen_opts_dict(body.generation_options)
    if opts:
        skeleton["generation_options"] = normalize_generation_options(
            {**(skeleton.get("generation_options") or {}), **opts}
        )

    layer = body.layer
    style_id = body.style_id or "simple"
    if layer in ("theme", "groove"):
        style_id = "simple"

    preset = resolve_ensemble(body.ensemble_id)
    inst = dict(preset.get("instruments") or {})
    if body.instruments is not None:
        inst.update(_instruments_dict(body.instruments) or {})

    if layer == "ensemble" and style_id == "simple":
        style_id = str(preset.get("default_style_id") or "simple")

    try:
        profile = _load_style_profile(style_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Style reference not found") from exc

    try:
        piece = render_skeleton(
            skeleton,
            profile,
            seed=body.seed,
            instruments=inst,
            include_midi=True,
            include_musicxml=False,
        )
        piece["layer"] = layer
        piece["ensemble_id"] = preset.get("id")
        piece["style_id"] = style_id
        return piece
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Lab render failed: {exc}") from exc


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
    try:
        profile = _load_style_profile(body.orchestra_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Orchestra not found") from exc
    try:
        return render_skeleton(
            body.skeleton,
            profile,
            seed=body.seed,
            instruments=_instruments_dict(body.instruments),
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
