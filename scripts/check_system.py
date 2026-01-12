"""快速系统检查脚本"""
import sys
sys.path.insert(0, 'src')

import torch
from sb3_contrib import MaskablePPO
from intelligent_meal_planner.rl.environment import MealPlanningEnv

print('='*60)
print('SYSTEM CHECK')
print('='*60)
print(f'PyTorch:     {torch.__version__}')
print(f'CUDA:        {torch.cuda.is_available()} ({torch.version.cuda if torch.cuda.is_available() else "N/A"})')
if torch.cuda.is_available():
    print(f'GPU:         {torch.cuda.get_device_name(0)}')
    print(f'GPU Memory:  {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB')
print()
env = MealPlanningEnv()
print('Environment: OK')
print(f'  Obs space: {env.observation_space.shape}')
print(f'  Act space: {env.action_space.n} recipes')
print()
print('MaskablePPO: OK')
print('='*60)
print('All checks passed! Ready to train.')
print('='*60)
