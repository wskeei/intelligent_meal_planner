"""分析模型是否陷入局部最优"""
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

# 加载模型
model_path = "models/ppo_meal_fast_final.zip"
stats_path = "models/vec_normalize_fast.pkl"

print("Loading model...")
model = MaskablePPO.load(model_path)

print("\n" + "=" * 70)
print("MODEL BEHAVIOR ANALYSIS")
print("=" * 70)

# 测试1: 固定目标，多次运行
print("\n[Test 1] Fixed target (2000 kcal), 10 episodes with deterministic=True")
print("-" * 70)

all_selections = []
for ep in range(10):
    def make_env():
        env = MealPlanningEnv(
            target_calories=2000.0,
            target_protein=100.0,
            target_carbs=250.0,
            target_fat=65.0,
            budget_limit=100.0,
            training_mode=False
        )
        return ActionMasker(env, mask_fn)

    env = make_vec_env(make_env, n_envs=1)
    env = VecNormalize.load(stats_path, env)
    env.training = False
    env.norm_reward = False

    obs = env.reset()
    episode_recipes = []

    for step in range(6):
        masks = env.env_method("action_masks")[0]
        action, _ = model.predict(obs, action_masks=masks, deterministic=True)
        obs, _, dones, infos = env.step(action)
        episode_recipes.append(infos[0]['selected_recipe'])

    all_selections.append(tuple(episode_recipes))
    env.close()

# 统计唯一组合数
unique_combinations = len(set(all_selections))
print(f"Unique meal combinations: {unique_combinations} / 10")
print(f"Selected recipes (sample): {all_selections[0]}")

# 测试2: 使用 deterministic=False 看看有没有随机性
print("\n[Test 2] Fixed target, 10 episodes with deterministic=False (stochastic)")
print("-" * 70)

all_selections_stochastic = []
for ep in range(10):
    def make_env():
        env = MealPlanningEnv(
            target_calories=2000.0,
            target_protein=100.0,
            target_carbs=250.0,
            target_fat=65.0,
            budget_limit=100.0,
            training_mode=False
        )
        return ActionMasker(env, mask_fn)

    env = make_vec_env(make_env, n_envs=1)
    env = VecNormalize.load(stats_path, env)
    env.training = False
    env.norm_reward = False

    obs = env.reset()
    episode_recipes = []

    for step in range(6):
        masks = env.env_method("action_masks")[0]
        action, _ = model.predict(obs, action_masks=masks, deterministic=False)  # 随机采样
        obs, _, dones, infos = env.step(action)
        episode_recipes.append(infos[0]['selected_recipe'])

    all_selections_stochastic.append(tuple(episode_recipes))
    env.close()

unique_stochastic = len(set(all_selections_stochastic))
print(f"Unique meal combinations: {unique_stochastic} / 10")

# 统计每个位置出现的菜品
print("\n[Analysis] Recipe frequency at each meal slot:")
print("-" * 70)
meals = ['Breakfast-1', 'Breakfast-2', 'Lunch-1', 'Lunch-2', 'Dinner-1', 'Dinner-2']
for i, meal in enumerate(meals):
    recipes_at_slot = [s[i] for s in all_selections_stochastic]
    unique = set(recipes_at_slot)
    print(f"  {meal}: {len(unique)} unique recipes")
    for r in unique:
        count = recipes_at_slot.count(r)
        print(f"    - {r}: {count}/10 ({count*10}%)")

# 测试3: 不同卡路里目标
print("\n[Test 3] Different calorie targets (deterministic=True)")
print("-" * 70)

targets = [1500, 1800, 2000, 2200, 2500]
for target in targets:
    def make_env():
        env = MealPlanningEnv(
            target_calories=float(target),
            target_protein=target * 0.2 / 4,
            target_carbs=target * 0.5 / 4,
            target_fat=target * 0.3 / 9,
            budget_limit=target * 0.05,  # 5元/100kcal
            training_mode=False
        )
        return ActionMasker(env, mask_fn)

    env = make_vec_env(make_env, n_envs=1)
    env = VecNormalize.load(stats_path, env)
    env.training = False
    env.norm_reward = False

    obs = env.reset()
    recipes = []
    for step in range(6):
        masks = env.env_method("action_masks")[0]
        action, _ = model.predict(obs, action_masks=masks, deterministic=True)
        obs, _, dones, infos = env.step(action)
        recipes.append(infos[0]['selected_recipe'][:8])  # 截取前8字符

    final_cal = infos[0]['total_calories']
    print(f"  {target} kcal: {recipes} -> {final_cal:.0f} kcal")
    env.close()

print("\n" + "=" * 70)
print("DIAGNOSIS")
print("=" * 70)
print("""
If unique combinations = 1 with deterministic=True:
  -> Model has converged to a single "optimal" solution
  -> This is expected behavior for a well-trained deterministic policy

If unique combinations = 1 even with deterministic=False:
  -> Model's policy is too peaked (low entropy)
  -> The model is very confident about its choices

If different targets produce same recipes:
  -> Model may not have learned to adapt to different targets
  -> Curriculum learning Stage 2/3 may need more training

RECOMMENDATIONS:
1. For production: Use deterministic=False with temperature sampling
2. For better diversity: Train with higher entropy coefficient
3. For target adaptation: Ensure curriculum learning progresses properly
""")
