# Linux Runtime Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让当前项目从原有 Windows 本地启动方式迁移到 Linux，可直接安装依赖、启动前后端、并完成基础功能验证。

**Architecture:** 保留现有 `uv + FastAPI + Vue/Vite` 技术栈与入口，新增 Linux shell 启动脚本，统一通过环境变量控制 API 端口与前端代理目标；同时把 README 和示例环境变量补齐为跨平台说明。对已有业务代码只做为 Linux 运行所需的最小调整，不做无关重构。

**Tech Stack:** Python, uv, FastAPI, Uvicorn, Vue 3, Vite, bash, pytest, npm

---

### Task 1: Inventory Existing Runtime Assumptions

**Files:**
- Modify: `docs/superpowers/plans/2026-04-02-linux-runtime-migration.md`
- Test: `README.md`
- Test: `start_project.bat`
- Test: `scripts/start_backend.bat`
- Test: `scripts/start_frontend.bat`

- [ ] **Step 1: Review startup entrypoints and env defaults**

```bash
sed -n '1,220p' README.md
sed -n '1,220p' start_project.bat
sed -n '1,220p' scripts/start_backend.bat
sed -n '1,220p' scripts/start_frontend.bat
sed -n '1,220p' frontend/src/api/config.ts
sed -n '1,220p' frontend/vite.config.ts
```

- [ ] **Step 2: Verify the Linux migration gap is real**

Run: `rg -n "\.bat|powershell|127\.0\.0\.1:9000|VITE_API|Scripts\\\\" .`
Expected: startup and local API configuration still contain Windows-oriented bootstrapping and hardcoded local defaults

- [ ] **Step 3: Commit the plan document**

```bash
git add docs/superpowers/plans/2026-04-02-linux-runtime-migration.md
git commit -m "docs: add linux runtime migration plan"
```

### Task 2: Add Linux Startup Scripts And Portable Env Defaults

**Files:**
- Create: `start_project.sh`
- Create: `scripts/start_backend.sh`
- Create: `scripts/start_frontend.sh`
- Modify: `.env.example`
- Modify: `frontend/src/api/config.ts`
- Modify: `frontend/vite.config.ts`
- Test: `start_project.sh`

- [ ] **Step 1: Write a failing shell validation check**

```bash
bash -n start_project.sh
```

Expected: FAIL because `start_project.sh` does not exist yet

- [ ] **Step 2: Add Linux startup scripts and portable env defaults**

```bash
cat > scripts/start_backend.sh <<'SH'
#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
API_PORT="${1:-${MEAL_PLANNER_API_PORT:-9000}}"
export PYTHONUTF8=1
export PYTHONIOENCODING=utf-8
cd "$ROOT_DIR"
exec uv run python -m uvicorn src.intelligent_meal_planner.api.main:app --reload --host 0.0.0.0 --port "$API_PORT"
SH
chmod +x scripts/start_backend.sh
```

```bash
cat > scripts/start_frontend.sh <<'SH'
#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
API_PORT="${1:-${MEAL_PLANNER_API_PORT:-9000}}"
export VITE_API_BASE_URL="${VITE_API_BASE_URL:-http://127.0.0.1:${API_PORT}/api}"
export VITE_API_PROXY_TARGET="${VITE_API_PROXY_TARGET:-http://127.0.0.1:${API_PORT}}"
cd "$ROOT_DIR/frontend"
exec npm run dev -- --host 0.0.0.0
SH
chmod +x scripts/start_frontend.sh
```

```bash
cat > start_project.sh <<'SH'
#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"
command -v uv >/dev/null
command -v npm >/dev/null
[ -d .venv ] || uv sync
[ -d frontend/node_modules ] || (cd frontend && npm install)
for p in $(seq 9000 9010) $(seq 18000 18010); do
  if python - <<PY
import socket
s = socket.socket()
try:
    s.bind(("127.0.0.1", $p))
except OSError:
    raise SystemExit(1)
finally:
    s.close()
PY
  then API_PORT="$p"; break; fi
done
: "${API_PORT:?no free port}"
nohup "$ROOT_DIR/scripts/start_backend.sh" "$API_PORT" > "$ROOT_DIR/backend.log" 2>&1 &
nohup "$ROOT_DIR/scripts/start_frontend.sh" "$API_PORT" > "$ROOT_DIR/frontend.log" 2>&1 &
printf 'Backend: http://127.0.0.1:%s\nFrontend: http://127.0.0.1:5173\nDocs: http://127.0.0.1:%s/docs\n' "$API_PORT" "$API_PORT"
SH
chmod +x start_project.sh
```

- [ ] **Step 3: Verify shell syntax and env wiring**

Run: `bash -n start_project.sh scripts/start_backend.sh scripts/start_frontend.sh`
Expected: exit 0 with no syntax errors

- [ ] **Step 4: Commit Linux startup support**

```bash
git add start_project.sh scripts/start_backend.sh scripts/start_frontend.sh .env.example frontend/src/api/config.ts frontend/vite.config.ts README.md
git commit -m "feat: add linux startup workflow"
```

### Task 3: Verify Backend, Frontend, And Tests On Linux

**Files:**
- Modify: `README.md`
- Test: `main.py`
- Test: `src/intelligent_meal_planner/api/main.py`
- Test: `frontend/package.json`
- Test: `tests/api/test_meal_chat_router.py`

- [ ] **Step 1: Run backend tests**

Run: `uv run pytest tests/api tests/meal_chat tests/test_main_cli.py -v`
Expected: all targeted tests pass, or failures identify the exact Linux/runtime blocker to fix

- [ ] **Step 2: Run frontend production build**

Run: `cd frontend && npm run build`
Expected: build completes successfully

- [ ] **Step 3: Smoke-start backend and frontend**

Run: `timeout 20s uv run python main.py api`
Expected: Uvicorn starts and logs startup before timeout stops it

Run: `timeout 20s ./scripts/start_frontend.sh 9000`
Expected: Vite starts and serves on `0.0.0.0:5173` before timeout stops it

- [ ] **Step 4: Commit docs/runtime verification adjustments**

```bash
git add README.md main.py frontend/package.json
git commit -m "docs: update linux deployment instructions"
```
