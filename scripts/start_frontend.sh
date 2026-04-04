#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
API_PORT="${1:-${MEAL_PLANNER_API_PORT:-9000}}"
FRONTEND_PORT="${2:-${MEAL_PLANNER_FRONTEND_PORT:-5173}}"
PID_FILE="${MEAL_PLANNER_FRONTEND_PID_FILE:-}"

export VITE_API_BASE_URL="${VITE_API_BASE_URL:-/api}"
export VITE_API_PROXY_TARGET="${VITE_API_PROXY_TARGET:-http://127.0.0.1:${API_PORT}}"

cd "$ROOT_DIR/frontend"

if [ -n "$PID_FILE" ]; then
  mkdir -p "$(dirname "$PID_FILE")"
  printf '%s\n' "$$" > "$PID_FILE"
fi

echo "[FRONTEND] Starting Vite dev server..."
echo "[FRONTEND] URL: http://127.0.0.1:${FRONTEND_PORT}"
echo "[FRONTEND] API proxy: ${VITE_API_PROXY_TARGET}"

exec npm run dev -- --host 0.0.0.0 --port "$FRONTEND_PORT" --strictPort
