import gymnasium as gym
import numpy as np
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.getcwd(), 'src'))

from intelligent_meal_planner.rl.environment import MealPlanningEnv

def test_env():
    env = MealPlanningEnv(training_mode=True)
    
    print("\n--- Testing Environment Reset ---")
    obs, info = env.reset()
    print(f"Target Calories: {env.target_calories:.1f}")
    print(f"Budget Limit: {env.budget_limit:.1f}")
    print(f"Observation shape: {obs.shape}")
    
    print("\n--- Testing Episode Loop ---")
    done = False
    total_reward = 0
    steps = 0
    
    while not done:
        # Use simple heuristic: pick random valid action roughly
        action = env.action_space.sample()
        obs, reward, terminated, truncated, info = env.step(action)
        done = terminated or truncated
        total_reward += reward
        steps += 1
        print(f"Step {steps}: Act={action}, Reward={reward:.2f}, Cost={info['total_cost']:.1f}, Cals={info['total_calories']:.1f}")
        
    print(f"\nFinal Total Reward: {total_reward:.2f}")
    print(f"Target vs Actual: Cals {env.target_calories:.1f} vs {env.total_calories:.1f}")
    print(f"Budget vs Actual: {env.budget_limit:.1f} vs {env.total_cost:.1f}")

if __name__ == "__main__":
    test_env()
