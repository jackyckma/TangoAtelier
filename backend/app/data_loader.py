from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "style_profiles"


def _profile_paths() -> list[Path]:
    return sorted(DATA_DIR.glob("*.json"))


@lru_cache(maxsize=1)
def _all_profiles() -> dict[str, dict]:
    profiles: dict[str, dict] = {}
    for path in _profile_paths():
        with path.open(encoding="utf-8") as fh:
            data = json.load(fh)
        orchestra_id = data["id"]
        profiles[orchestra_id] = data
    return profiles


def list_orchestras() -> list[dict]:
    """Return list cards (without full bio payloads for index)."""
    cards: list[dict] = []
    for profile in _all_profiles().values():
        cards.append(
            {
                "id": profile["id"],
                "name": profile["name"],
                "personality_type": profile["personality_type"],
                "personality_emoji": profile["personality_emoji"],
                "era": profile["era"],
                "sound_description": profile["sound_description"],
            }
        )
    order = ["d_arienzo", "biagi", "troilo", "di_sarli", "canaro", "pugliese"]
    cards.sort(key=lambda c: order.index(c["id"]) if c["id"] in order else 99)
    return cards


def load_orchestra(orchestra_id: str) -> dict:
    profiles = _all_profiles()
    if orchestra_id not in profiles:
        raise FileNotFoundError(orchestra_id)
    return profiles[orchestra_id]
