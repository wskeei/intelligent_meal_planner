"""
DQN 模型详细测试脚本

显示每个 episode 的详细配餐结果
"""

import sys
import json
from pathlib import Path

import numpy as np

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from intelligent_meal_planner.rl.environment import MealPlanningEnv
from intelligent_meal_planner.rl.dqn import MaskableDQNAgent

# 加载菜谱数据
RECIPES_PATH = project_root / "src" / "intelligent_meal_planner" / "data" / "recipes.json"
with open(RECIPES_PATH, 'r', encoding='utf-8') as f:
    data = json.load(f)
    RECIPES = data['recipes']  # 菜谱列表在 'recipes' 键下


def test_model(model_path: str = None, n_episodes: int = 5):
    """详细测试模型"""
    model_dir = project_root / "models"
    model_path = model_path or (model_dir / "dqn_meal_final.pt")

    print(f"加载模型: {model_path}")
    agent = MaskableDQNAgent.from_pretrained(str(model_path))

    env = MealPlanningEnv(training_mode=False)

    results = []
    for ep in range(n_episodes):
        obs, _ = env.reset()
        mask = env.action_masks()
        done = False

        print(f"\n{'='*60}")
        print(f"Episode {ep + 1}")
        print(f"目标: {env.target_calories:.0f} kcal, 预算: {env.budget_limit:.0f} 元")
        print(f"{'='*60}")

        meal_names = ['早餐', '午餐', '晚餐']
        current_meal = -1

        while not done:
            # 检查餐次变化
            step_meal = env.current_step_idx // 2
            if step_meal != current_meal:
                current_meal = step_meal
                print(f"\n--- {meal_names[current_meal]} ---")

            action = agent.select_action(obs, mask, step=500000, deterministic=True)
            obs, reward, terminated, truncated, info = env.step(action)
            done = terminated or truncated
            mask = env.action_masks()

            # 打印选择的菜品
            recipe = RECIPES[action]
            print(f"  {recipe['name']}: {recipe['calories']} kcal, {recipe['price']}元")

        # 统计结果
        cal_error = abs(env.total_calories - env.target_calories) / env.target_calories * 100
        budget_usage = env.total_cost / env.budget_limit * 100

        print(f"\n--- 结果 ---")
        print(f"总卡路里: {env.total_calories:.0f} / {env.target_calories:.0f} (误差: {cal_error:.1f}%)")
        print(f"总花费: {env.total_cost:.1f} / {env.budget_limit:.0f} 元 ({budget_usage:.1f}%)")

        results.append({
            'reward': info.get('episode_reward', 0),
            'cal_error': cal_error,
            'budget_usage': budget_usage,
        })

    # 汇总
    print(f"\n{'='*60}")
    print(f"测试汇总 ({n_episodes} episodes)")
    print(f"{'='*60}")
    print(f"平均卡路里误差: {np.mean([r['cal_error'] for r in results]):.1f}%")
    print(f"平均预算使用: {np.mean([r['budget_usage'] for r in results]):.1f}%")


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', type=str, default=None)
    parser.add_argument('--episodes', type=int, default=5)
    args = parser.parse_args()

    test_model(args.model, args.episodes)
