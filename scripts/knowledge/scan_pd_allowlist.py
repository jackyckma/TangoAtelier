#!/usr/bin/env python3
"""Scan PDMX metadata CSV for PD/CC0 tango-adjacent entries (metadata only).

Reads PDMX.csv from PDMX_CSV env or docs/research/knowledge/_cache/PDMX.csv.
Does NOT download score files or call MuseScore.com — metadata scan only.
"""

from __future__ import annotations

import csv
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CACHE = ROOT / "docs/research/knowledge/_cache/PDMX.csv"
OUTPUT = ROOT / "docs/research/knowledge/pd_allowlist.json"
POLICY_REF = "docs/research/KNOWLEDGE_SOURCE_POLICY.md"

TANGO_KEYWORDS = re.compile(
    r"tango|milonga|vals|waltz|habanera|bandoneon",
    re.IGNORECASE,
)
PD_LICENSE = re.compile(
    r"public\s*domain|cc[\s-]?0|pdm\b|pd\b",
    re.IGNORECASE,
)

NO_CSV_NOTE = (
    "No PDMX.csv found. To populate this ledger, download PDMX metadata only from "
    "https://zenodo.org/records/15571083 (PDMX.csv — not score bytes) and place it at "
    "docs/research/knowledge/_cache/PDMX.csv or set PDMX_CSV to its path, then re-run "
    "this script. Do not download MusicXML/MXL/PDF/MID or scrape MuseScore.com."
)

TAG_COLUMNS = frozenset(
    {"tags", "tag", "genre", "genres", "description", "title", "composer"}
)
LICENSE_COLUMNS = frozenset({"license", "license_url", "license_conflict"})


def _resolve_csv_path() -> Path | None:
    env = os.environ.get("PDMX_CSV", "").strip()
    if env:
        p = Path(env)
        return p if p.is_file() else None
    return DEFAULT_CACHE if DEFAULT_CACHE.is_file() else None


def _row_text(row: dict[str, str]) -> str:
    parts: list[str] = []
    for key, val in row.items():
        if val:
            parts.append(f"{key}:{val}")
    return " ".join(parts)


def _license_ok(row: dict[str, str]) -> tuple[bool, str]:
    license_bits: list[str] = []
    for col in LICENSE_COLUMNS:
        val = (row.get(col) or "").strip()
        if val:
            license_bits.append(val)
    tags = (row.get("tags") or row.get("tag") or "").strip()
    if tags:
        license_bits.append(tags)
    combined = " | ".join(license_bits) if license_bits else _row_text(row)
    if PD_LICENSE.search(combined):
        return True, combined
    return False, combined


def _tango_match(row: dict[str, str]) -> tuple[bool, str]:
    haystack_parts: list[str] = []
    for col in TAG_COLUMNS:
        val = (row.get(col) or "").strip()
        if val:
            haystack_parts.append(val)
    path = (row.get("path") or row.get("metadata") or "").strip()
    if path:
        haystack_parts.append(path)
    haystack = " ".join(haystack_parts) if haystack_parts else _row_text(row)
    if TANGO_KEYWORDS.search(haystack):
        return True, haystack[:500]
    return False, haystack[:500]


def _entry_id(row: dict[str, str], row_idx: int) -> str:
    for col in ("id", "path", "metadata"):
        val = (row.get(col) or "").strip()
        if val:
            stem = Path(val).stem
            if stem:
                return stem
    return f"pdmx-row-{row_idx}"


def _entry_title(row: dict[str, str], entry_id: str) -> str:
    for col in ("title", "name", "work_title"):
        val = (row.get(col) or "").strip()
        if val:
            return val
    return entry_id


def _entry_tags(row: dict[str, str]) -> str:
    bits: list[str] = []
    for col in ("tags", "tag", "genre", "genres"):
        val = (row.get(col) or "").strip()
        if val:
            bits.append(val)
    return "; ".join(bits)


def scan_csv(csv_path: Path) -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
    with csv_path.open(newline="", encoding="utf-8", errors="replace") as fh:
        reader = csv.DictReader(fh)
        for idx, row in enumerate(reader, start=1):
            normalized = {k: (v or "") for k, v in row.items() if k}
            lic_ok, license_text = _license_ok(normalized)
            if not lic_ok:
                continue
            tang_ok, match_text = _tango_match(normalized)
            if not tang_ok:
                continue
            eid = _entry_id(normalized, idx)
            entries.append(
                {
                    "id": eid,
                    "title": _entry_title(normalized, eid),
                    "license": license_text[:300],
                    "tags": _entry_tags(normalized),
                    "reason": f"PD/CC0 license + tango-adjacent text match ({match_text[:200]})",
                }
            )
    return entries


def build_allowlist(csv_path: Path | None) -> dict:
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    meta: dict[str, str] = {
        "generated_at": now,
        "source": str(csv_path) if csv_path else "none",
        "policy_ref": POLICY_REF,
    }
    if csv_path is None:
        meta["note"] = NO_CSV_NOTE
        return {"meta": meta, "entries": []}
    entries = scan_csv(csv_path)
    meta["note"] = (
        f"Scanned {csv_path.name}; {len(entries)} tango-adjacent PD/CC0 rows. "
        "Empty entries are valid — PDMX tango-adjacent coverage is known-sparse."
    )
    return {"meta": meta, "entries": entries}


def main() -> int:
    csv_path = _resolve_csv_path()
    allowlist = build_allowlist(csv_path)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(allowlist, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {OUTPUT} ({len(allowlist['entries'])} entries)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
