#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
API_PORT="${1:-${MEAL_PLANNER_API_PORT:-9000}}"

export VITE_API_BASE_URL="${VITE_API_BASE_URL:-/api}"
export VITE_API_PROXY_TARGET="${VITE_API_PROXY_TARGET:-http://127.0.0.1:${API_PORT}}"

cd "$ROOT_DIR/frontend"

echo "[FRONTEND] Starting Vite dev server..."
echo "[FRONTEND] URL: http://127.0.0.1:5173"
echo "[FRONTEND] API proxy: ${VITE_API_PROXY_TARGET}"

exec npm run dev -- --host 0.0.0.0
