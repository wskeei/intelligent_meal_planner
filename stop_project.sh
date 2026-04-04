#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUN_DIR="$ROOT_DIR/.run"

echo "[INFO] Intelligent Meal Planner shutdown"
echo "[INFO] Project root: $ROOT_DIR"

collect_descendants() {
  local parent_pid="$1"
  local child_pid

  if ! command -v pgrep >/dev/null 2>&1; then
    return 0
  fi

  while read -r child_pid; do
    [ -n "$child_pid" ] || continue
    collect_descendants "$child_pid"
    echo "$child_pid"
  done < <(pgrep -P "$parent_pid" 2>/dev/null || true)
}

terminate_pid_tree() {
  local pid="$1"
  local label="$2"
  local child_pid
  local descendants

  descendants="$(collect_descendants "$pid")"

  while read -r child_pid; do
    [ -n "$child_pid" ] || continue
    kill "$child_pid" 2>/dev/null || true
  done <<< "$descendants"

  kill "$pid" 2>/dev/null || true
  sleep 1

  while read -r child_pid; do
    [ -n "$child_pid" ] || continue
    kill -0 "$child_pid" 2>/dev/null && kill -9 "$child_pid" 2>/dev/null || true
  done <<< "$descendants"

  kill -0 "$pid" 2>/dev/null && kill -9 "$pid" 2>/dev/null || true
  echo "[INFO] Stopped ${label} (pid ${pid})"
}

stop_from_pidfile() {
  local label="$1"
  local pid_file="$2"
  local pid

  if [ ! -f "$pid_file" ]; then
    return 1
  fi

  pid="$(tr -d '[:space:]' < "$pid_file")"
  if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
    terminate_pid_tree "$pid" "$label"
    rm -f "$pid_file"
    return 0
  else
    echo "[WARN] ${label} pid file is stale: $pid_file"
    rm -f "$pid_file"
    return 1
  fi
}

fallback_shutdown() {
  echo "[INFO] Falling back to process-pattern shutdown"
  pkill -f "scripts/start_backend.sh" 2>/dev/null || true
  pkill -f "uvicorn src.intelligent_meal_planner.api.main:app" 2>/dev/null || true
  pkill -f "scripts/start_frontend.sh" 2>/dev/null || true
  pkill -f "vite.js --host 0.0.0.0" 2>/dev/null || true
}

stopped_any=0

if stop_from_pidfile "backend" "$RUN_DIR/backend.pid"; then
  stopped_any=1
fi

if stop_from_pidfile "frontend" "$RUN_DIR/frontend.pid"; then
  stopped_any=1
fi

if [ "$stopped_any" -eq 0 ]; then
  fallback_shutdown
else
  pkill -f "uvicorn src.intelligent_meal_planner.api.main:app" 2>/dev/null || true
  pkill -f "vite.js --host 0.0.0.0" 2>/dev/null || true
fi

if [ -d "$RUN_DIR" ]; then
  rmdir "$RUN_DIR" 2>/dev/null || true
fi

echo "[INFO] Shutdown complete"
