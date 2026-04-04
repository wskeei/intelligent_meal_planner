#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUN_DIR="$ROOT_DIR/.run"
cd "$ROOT_DIR"

echo "[INFO] Intelligent Meal Planner startup"
echo "[INFO] Project root: $ROOT_DIR"

if ! command -v uv >/dev/null 2>&1; then
  echo "[ERROR] uv not found in PATH. Install uv first."
  exit 1
fi

if ! command -v npm >/dev/null 2>&1; then
  echo "[ERROR] npm not found in PATH. Install Node.js first."
  exit 1
fi

if [ ! -d ".venv" ]; then
  echo "[INFO] Python environment missing. Running uv sync..."
  uv sync
else
  echo "[INFO] Python environment found."
fi

if [ ! -d "frontend/node_modules" ]; then
  echo "[INFO] Frontend dependencies missing. Running npm install..."
  (
    cd frontend
    npm install
  )
else
  echo "[INFO] Frontend dependencies found."
fi

if [ -x "$ROOT_DIR/.venv/bin/python" ]; then
  PYTHON_BIN="$ROOT_DIR/.venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN="$(command -v python3)"
else
  echo "[ERROR] Python interpreter not found. Run uv sync first."
  exit 1
fi

find_free_port() {
  local start_port="$1"
  local end_port="$2"
  local port
  for port in $(seq "$start_port" "$end_port"); do
    if "$PYTHON_BIN" - "$port" <<'PY'
import socket
import sys

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    sock.bind(("127.0.0.1", int(sys.argv[1])))
except OSError:
    raise SystemExit(1)
finally:
    sock.close()
PY
    then
      echo "$port"
      return 0
    fi
  done

  return 1
}

API_PORT="${MEAL_PLANNER_API_PORT:-$(find_free_port 9000 9010 || find_free_port 18000 18010)}"
FRONTEND_PORT="${MEAL_PLANNER_FRONTEND_PORT:-$(find_free_port 5173 5183 || find_free_port 15173 15183)}"

if [ -z "$API_PORT" ]; then
  echo "[ERROR] Could not find an available backend port."
  exit 1
fi

if [ -z "$FRONTEND_PORT" ]; then
  echo "[ERROR] Could not find an available frontend port."
  exit 1
fi

echo "[INFO] Selected backend port: $API_PORT"
echo "[INFO] Selected frontend port: $FRONTEND_PORT"

mkdir -p "$RUN_DIR"
BACKEND_PID_FILE="$RUN_DIR/backend.pid"
FRONTEND_PID_FILE="$RUN_DIR/frontend.pid"
rm -f "$BACKEND_PID_FILE" "$FRONTEND_PID_FILE"

echo "[INFO] Starting backend..."
nohup env MEAL_PLANNER_BACKEND_PID_FILE="$BACKEND_PID_FILE" \
  "$ROOT_DIR/scripts/start_backend.sh" "$API_PORT" > "$ROOT_DIR/backend.log" 2>&1 &
BACKEND_PID=$!

echo "[INFO] Starting frontend..."
nohup env MEAL_PLANNER_FRONTEND_PID_FILE="$FRONTEND_PID_FILE" \
  "$ROOT_DIR/scripts/start_frontend.sh" "$API_PORT" "$FRONTEND_PORT" > "$ROOT_DIR/frontend.log" 2>&1 &
FRONTEND_PID=$!

echo "[INFO] Backend PID: $BACKEND_PID"
echo "[INFO] Frontend PID: $FRONTEND_PID"
echo "[INFO] Backend:  http://127.0.0.1:$API_PORT"
echo "[INFO] Frontend: http://127.0.0.1:$FRONTEND_PORT"
echo "[INFO] API Docs: http://127.0.0.1:$API_PORT/docs"
echo "[INFO] Logs: backend.log / frontend.log"
echo "[INFO] Stop: ./stop_project.sh"
