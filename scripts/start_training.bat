@echo off
REM DQN 训练启动脚本

echo ============================================================
echo     Intelligent Meal Planner - DQN Training
echo ============================================================
echo.
echo Starting DQN training with the project defaults.
echo.

call conda activate ai_lab

python -c "import torch; print(f'CUDA: {torch.cuda.is_available()}')"

echo.
echo Starting training...
echo Monitor with: tensorboard --logdir models/logs/tensorboard/dqn
echo.
echo ============================================================

python scripts/train_dqn_maskable.py --timesteps 500000

echo.
echo Training finished!
pause
