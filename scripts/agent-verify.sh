#!/usr/bin/env bash
# Minimal L0+L1 verification for AI agents (especially Cloud Agents).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "==> agent-verify (project: $ROOT)"

echo "==> L0: frontend typecheck"
(
  cd frontend
  pnpm exec tsc -b --pretty false
)

if [[ -x "$ROOT/backend/.venv/bin/python" ]]; then
  echo "==> L1: backend style profile load"
  (
    cd backend
    .venv/bin/python -c 'from app.data_loader import list_orchestras; assert len(list_orchestras()) == 6'
  )
else
  echo "WARN: backend/.venv missing — skip L1 (create venv + pip install -r backend/requirements.txt)"
fi

echo "==> agent-verify OK"
