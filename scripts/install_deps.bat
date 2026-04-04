@echo off
REM 安装 DQN 训练与运行所需的依赖到 ai_lab 环境

echo ============================================================
echo Installing dependencies for the DQN meal planner stack
echo ============================================================

call conda activate ai_lab

echo.
echo [1/2] Installing PyTorch and core training dependencies...
pip install torch tensorboard -q

echo.
echo [2/2] Installing project dependencies...
pip install -e . -q

echo.
echo ============================================================
echo Installation complete!
echo.
echo To start DQN training, run:
echo   conda activate ai_lab
echo   python scripts/train_dqn_maskable.py --timesteps 500000
echo ============================================================
pause
