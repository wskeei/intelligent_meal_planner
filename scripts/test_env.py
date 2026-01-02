"""
Verification script for MealPlanningEnv.
Checks if the environment correctly handles 9 steps per episode and accumulates calories.
"""
import sys
from pathlib import Path
import numpy as np

# Ensure src is in python path
current_dir = Path(__file__).resolve().parent
src_path = current_dir.parent / "src"
sys.path.append(str(src_path))

from intelligent_meal_planner.rl.environment import MealPlanningEnv

def test_environment():
    print("Initializing environment...")
    env = MealPlanningEnv()
    
    obs, info = env.reset()
    print("Environment reset.")
    
    # Check max steps
    print(f"Max steps: {env.max_steps} (Expected: 9)")
    if env.max_steps != 9:
        print("FAIL: Max steps incorrect.")
        return
        
    terminated = False
    step_count = 0
    total_reward = 0
    
    print("\nStarting simulation...")
    while not terminated:
        # Random action
        action = env.action_space.sample()
        
        # Taking step
        obs, reward, terminated, truncated, info = env.step(action)
        step_count += 1
        total_reward += reward
        
        print(f"Step {step_count}: Selected {info.get('selected_recipe', 'Unknown')} | Current Cals: {info.get('total_calories', 0):.1f}")
        
    print(f"\nSimulation finished in {step_count} steps.")
    print(f"Total Cals: {env.total_calories:.1f}")
    
    if step_count == 9:
        print("PASS: Episode length is correct (9 steps).")
    else:
        print(f"FAIL: Episode length is {step_count} (Expected 9).")
        
    if env.total_calories > 1000:
        print("PASS: Calorie accumulation seems reasonable (>1000).")
    else:
        print("WARNING: Total calories seems low. Check if random actions are picking small items.")

if __name__ == "__main__":
    test_environment()
