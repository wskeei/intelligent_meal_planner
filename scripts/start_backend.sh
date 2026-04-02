#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
API_PORT="${1:-${MEAL_PLANNER_API_PORT:-9000}}"

export PYTHONUTF8=1
export PYTHONIOENCODING=utf-8

cd "$ROOT_DIR"

echo "[BACKEND] Starting FastAPI server..."
echo "[BACKEND] URL: http://127.0.0.1:${API_PORT}"
echo "[BACKEND] Docs: http://127.0.0.1:${API_PORT}/docs"

exec uv run python -m uvicorn src.intelligent_meal_planner.api.main:app --reload --host 0.0.0.0 --port "$API_PORT"
