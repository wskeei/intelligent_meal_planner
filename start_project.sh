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

STARTUP_CHECK_ENABLED="${MEAL_PLANNER_STARTUP_CHECK:-1}"
STARTUP_TIMEOUT_SECONDS="${MEAL_PLANNER_STARTUP_TIMEOUT_SECONDS:-20}"

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

is_port_open() {
  "$PYTHON_BIN" - "$1" <<'PY'
import socket
import sys

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.settimeout(0.2)
try:
    if sock.connect_ex(("127.0.0.1", int(sys.argv[1]))) != 0:
        raise SystemExit(1)
finally:
    sock.close()
PY
}

is_pid_running_from_file() {
  local pid_file="$1"
  local pid

  if [ ! -f "$pid_file" ]; then
    return 1
  fi

  pid="$(tr -d '[:space:]' < "$pid_file" 2>/dev/null || true)"
  if [ -z "$pid" ]; then
    return 1
  fi

  kill -0 "$pid" 2>/dev/null
}

report_startup_failure() {
  local service_name="$1"
  local port="$2"
  local pid_file="$3"
  local log_file="$4"

  echo "[ERROR] ${service_name} failed to stay running on http://127.0.0.1:${port}"
  if [ -f "$pid_file" ]; then
    echo "[ERROR] PID file: $pid_file"
  fi
  echo "[ERROR] Recent ${service_name} log:"
  tail -n 40 "$log_file" 2>/dev/null || true
}

wait_for_service() {
  local service_name="$1"
  local port="$2"
  local pid_file="$3"
  local log_file="$4"
  local attempts

  attempts=$((STARTUP_TIMEOUT_SECONDS * 10))
  if [ "$attempts" -lt 1 ]; then
    attempts=1
  fi

  for _ in $(seq 1 "$attempts"); do
    if is_port_open "$port"; then
      return 0
    fi

    if [ -f "$pid_file" ] && ! is_pid_running_from_file "$pid_file"; then
      report_startup_failure "$service_name" "$port" "$pid_file" "$log_file"
      return 1
    fi

    sleep 0.1
  done

  echo "[ERROR] Timed out waiting for ${service_name} at http://127.0.0.1:${port}"
  report_startup_failure "$service_name" "$port" "$pid_file" "$log_file"
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
  bash "$ROOT_DIR/scripts/start_backend.sh" "$API_PORT" > "$ROOT_DIR/backend.log" 2>&1 &
BACKEND_PID=$!

echo "[INFO] Starting frontend..."
nohup env MEAL_PLANNER_FRONTEND_PID_FILE="$FRONTEND_PID_FILE" \
  bash "$ROOT_DIR/scripts/start_frontend.sh" "$API_PORT" "$FRONTEND_PORT" > "$ROOT_DIR/frontend.log" 2>&1 &
FRONTEND_PID=$!

echo "[INFO] Backend PID: $BACKEND_PID"
echo "[INFO] Frontend PID: $FRONTEND_PID"
echo "[INFO] Backend:  http://127.0.0.1:$API_PORT"
echo "[INFO] Frontend: http://127.0.0.1:$FRONTEND_PORT"
echo "[INFO] API Docs: http://127.0.0.1:$API_PORT/docs"
echo "[INFO] Logs: backend.log / frontend.log"
echo "[INFO] Stop: ./stop_project.sh"

if [ "$STARTUP_CHECK_ENABLED" != "0" ]; then
  if ! wait_for_service "Backend" "$API_PORT" "$BACKEND_PID_FILE" "$ROOT_DIR/backend.log"; then
    bash "$ROOT_DIR/stop_project.sh" >/dev/null 2>&1 || true
    exit 1
  fi

  if ! wait_for_service "Frontend" "$FRONTEND_PORT" "$FRONTEND_PID_FILE" "$ROOT_DIR/frontend.log"; then
    bash "$ROOT_DIR/stop_project.sh" >/dev/null 2>&1 || true
    exit 1
  fi

  echo "[INFO] Startup check passed"
fi
