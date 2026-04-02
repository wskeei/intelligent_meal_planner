@echo off
setlocal
chcp 65001 >nul

set "ROOT_DIR=%~dp0.."
cd /d "%ROOT_DIR%"
set "API_PORT=%~1"

if "%API_PORT%"=="" set "API_PORT=9000"

echo [BACKEND] Starting FastAPI server...
echo [BACKEND] URL: http://127.0.0.1:%API_PORT%
echo [BACKEND] Docs: http://127.0.0.1:%API_PORT%/docs

set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"

call uv run python -m uvicorn src.intelligent_meal_planner.api.main:app --reload --host 0.0.0.0 --port %API_PORT%

if errorlevel 1 (
    echo [BACKEND] Server exited with an error.
)
