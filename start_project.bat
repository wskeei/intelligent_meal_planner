@echo off
setlocal
chcp 65001 >nul

set "ROOT_DIR=%~dp0"
cd /d "%ROOT_DIR%"

echo [INFO] Intelligent Meal Planner startup
echo [INFO] Project root: %ROOT_DIR%

where uv >nul 2>nul
if errorlevel 1 (
    echo [ERROR] uv not found in PATH. Install uv first.
    pause
    exit /b 1
)

where npm >nul 2>nul
if errorlevel 1 (
    echo [ERROR] npm not found in PATH. Install Node.js first.
    pause
    exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
    echo [INFO] Python environment missing. Running uv sync...
    call uv sync
    if errorlevel 1 (
        echo [ERROR] uv sync failed.
        pause
        exit /b 1
    )
) else (
    echo [INFO] Python environment found.
)

if not exist "frontend\node_modules" (
    echo [INFO] Frontend dependencies missing. Running npm install...
    pushd "frontend"
    call npm install
    set "NPM_STATUS=%ERRORLEVEL%"
    popd
    if not "%NPM_STATUS%"=="0" (
        echo [ERROR] npm install failed.
        pause
        exit /b 1
    )
) else (
    echo [INFO] Frontend dependencies found.
)

for /f %%P in ('powershell -NoProfile -Command "$ports = 9000..9010 + 18000..18010; foreach ($p in $ports) { try { $listener = [System.Net.Sockets.TcpListener]::new([Net.IPAddress]::Loopback, $p); $listener.Start(); $listener.Stop(); Write-Output $p; break } catch {} }"') do set "API_PORT=%%P"

if not defined API_PORT (
    echo [ERROR] Could not find an available backend port.
    pause
    exit /b 1
)

echo [INFO] Selected backend port: %API_PORT%

echo [INFO] Starting backend window...
powershell -NoProfile -Command "Start-Process -FilePath '%ROOT_DIR%scripts\start_backend.bat' -WorkingDirectory '%ROOT_DIR%' -WindowStyle Normal -ArgumentList '%API_PORT%'"

echo [INFO] Starting frontend window...
powershell -NoProfile -Command "Start-Process -FilePath '%ROOT_DIR%scripts\start_frontend.bat' -WorkingDirectory '%ROOT_DIR%' -WindowStyle Normal -ArgumentList '%API_PORT%'"

echo [INFO] Backend:  http://127.0.0.1:%API_PORT%
echo [INFO] Frontend: http://localhost:5173
echo [INFO] API Docs: http://127.0.0.1:%API_PORT%/docs
exit /b 0
