from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.data_loader import list_orchestras, load_orchestra

app = FastAPI(title="TangoAtelier API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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


@app.get("/")
def root() -> dict[str, str]:
    return {
        "service": "TangoAtelier API",
        "docs": "/docs",
        "health": "/health",
    }


def data_dir() -> Path:
    return Path(__file__).resolve().parent.parent / "data" / "style_profiles"
