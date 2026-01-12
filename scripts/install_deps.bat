@echo off
REM 安装训练所需的依赖到 ai_lab 环境
REM 运行方式: 双击此文件 或 在命令行中运行 install_deps.bat

echo ============================================================
echo Installing dependencies for meal planner RL training
echo ============================================================

REM 激活 ai_lab 环境并安装依赖
call conda activate ai_lab

echo.
echo [1/3] Installing stable-baselines3...
pip install stable-baselines3[extra] -q

echo.
echo [2/3] Installing sb3-contrib (for MaskablePPO)...
pip install sb3-contrib -q

echo.
echo [3/3] Installing other dependencies...
pip install tqdm rich -q

echo.
echo ============================================================
echo Installation complete!
echo.
echo To start training, run:
echo   conda activate ai_lab
echo   python scripts/train_optimized.py
echo ============================================================
pause
