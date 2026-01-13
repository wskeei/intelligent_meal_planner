"""详细测试模型 - 查看具体选择了哪些菜品"""
import sys
sys.path.insert(0, 'src')

import numpy as np
from pathlib import Path
from sb3_contrib import MaskablePPO
from sb3_contrib.common.wrappers import ActionMasker
from stable_baselines3.common.env_util import make_vec_env
from stable_baselines3.common.vec_env import VecNormalize

from intelligent_meal_planner.rl.environment import MealPlanningEnv

def mask_fn(env):
    return env.get_wrapper_attr("action_masks")()

def make_test_env(randomize=False):
    env = MealPlanningEnv(
        target_calories=2000.0,
        target_protein=100.0,
        target_carbs=250.0,
        target_fat=65.0,
        budget_limit=100.0,  # 根据中国菜谱调整
        training_mode=randomize
    )
    env = ActionMasker(env, mask_fn)
    return env

# 加载模型
model_path = "models/ppo_meal_fast_final.zip"
stats_path = "models/vec_normalize_fast.pkl"

print("Loading model...")
model = MaskablePPO.load(model_path)

# 测试固定目标
print("\n" + "=" * 70)
print("TEST 1: Fixed Target (2000 kcal, 100 yuan budget)")
print("=" * 70)

env = make_vec_env(lambda: make_test_env(False), n_envs=1)
env = VecNormalize.load(stats_path, env)
env.training = False
env.norm_reward = False

obs = env.reset()
done = False
step = 0
meals = {0: "Breakfast-1", 1: "Breakfast-2", 2: "Lunch-1", 3: "Lunch-2", 4: "Dinner-1", 5: "Dinner-2"}

print(f"\nTarget: {env.get_attr('target_calories')[0]:.0f} kcal, Budget: {env.get_attr('budget_limit')[0]:.0f} yuan")
print("-" * 70)

while not done:
    masks = env.env_method("action_masks")[0]
    action, _ = model.predict(obs, action_masks=masks, deterministic=True)
    obs, rewards, dones, infos = env.step(action)

    info = infos[0]
    recipe = info.get('selected_recipe', 'Unknown')
    print(f"  {meals[step]}: {recipe}")

    step += 1
    done = dones[0]

print("-" * 70)
print(f"Total Calories: {info.get('total_calories', 0):.0f} / {env.get_attr('target_calories')[0]:.0f}")
print(f"Total Cost: {info.get('total_cost', 0):.1f} / {env.get_attr('budget_limit')[0]:.0f} yuan")
print(f"Unique Categories: {info.get('unique_categories', 0)}")

env.close()

# 测试随机目标
print("\n" + "=" * 70)
print("TEST 2: Random Targets (Domain Randomization)")
print("=" * 70)

for i in range(3):
    env = make_vec_env(lambda: make_test_env(True), n_envs=1)
    env = VecNormalize.load(stats_path, env)
    env.training = False
    env.norm_reward = False

    obs = env.reset()
    target_cal = env.get_attr('target_calories')[0]
    budget = env.get_attr('budget_limit')[0]

    print(f"\n--- Episode {i+1}: Target {target_cal:.0f} kcal, Budget {budget:.0f} yuan ---")

    done = False
    step = 0
    while not done:
        masks = env.env_method("action_masks")[0]
        action, _ = model.predict(obs, action_masks=masks, deterministic=True)
        obs, rewards, dones, infos = env.step(action)

        info = infos[0]
        recipe = info.get('selected_recipe', 'Unknown')
        print(f"  {meals[step]}: {recipe}")

        step += 1
        done = dones[0]

    final_cal = info.get('total_calories', 0)
    cal_error = abs(final_cal - target_cal) / target_cal * 100
    print(f"  Result: {final_cal:.0f}/{target_cal:.0f} kcal ({cal_error:.1f}% error), Cost: {info.get('total_cost', 0):.1f} yuan")

    env.close()

print("\n" + "=" * 70)
