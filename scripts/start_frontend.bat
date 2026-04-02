@echo off
setlocal
chcp 65001 >nul

set "ROOT_DIR=%~dp0.."
set "API_PORT=%~1"
if "%API_PORT%"=="" set "API_PORT=9000"

set "VITE_API_BASE_URL=http://127.0.0.1:%API_PORT%/api"
set "VITE_API_PROXY_TARGET=http://127.0.0.1:%API_PORT%"

cd /d "%ROOT_DIR%\frontend"

echo [FRONTEND] Starting Vite dev server...
echo [FRONTEND] URL: http://localhost:5173
echo [FRONTEND] API: %VITE_API_BASE_URL%

call npm run dev

if errorlevel 1 (
    echo [FRONTEND] Dev server exited with an error.
)
