@echo off
REM 高性能训练启动脚本
REM 优化配置: RTX 4060 (8GB) + 24核CPU + 32GB RAM

echo ============================================================
echo     Intelligent Meal Planner - High Performance Training
echo ============================================================
echo.
echo Hardware Profile:
echo   GPU:  RTX 4060 Laptop (8GB VRAM)
echo   CPU:  24 cores / 32 threads
echo   RAM:  32GB
echo.
echo Optimized Settings:
echo   - 24 parallel environments (SubprocVecEnv)
echo   - Batch size: 512
echo   - Buffer: 6144 samples
echo   - Curriculum Learning enabled
echo.

REM 激活环境
call conda activate ai_lab

REM 检查CUDA
python -c "import torch; print(f'CUDA: {torch.cuda.is_available()}')"

echo.
echo Starting training...
echo Monitor with: tensorboard --logdir models/logs/tensorboard
echo.
echo ============================================================

REM 运行训练
python scripts/train_optimized.py --mode train --timesteps 500000

echo.
echo Training finished!
pause
