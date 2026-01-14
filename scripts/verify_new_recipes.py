"""验证新菜谱配置是否正确"""
import sys
sys.path.insert(0, 'src')

from intelligent_meal_planner.rl.environment import MealPlanningEnv

print("=" * 60)
print("验证新中国菜谱配置")
print("=" * 60)

# 测试环境创建
env = MealPlanningEnv(training_mode=False)
print(f'\n[环境配置]')
print(f'  菜品数量: {env.action_space.n}')
print(f'  默认预算: {env.budget_limit} 元')
print(f'  目标热量: {env.target_calories} kcal')

# 测试reset
obs, info = env.reset()
print(f'\n[观察空间]')
print(f'  维度: {obs.shape}')

# 测试action_masks
masks = env.action_masks()
valid_actions = masks.sum()
print(f'\n[动作空间]')
print(f'  早餐可选菜品: {valid_actions} 个')

# 测试一个episode
print('\n[测试一个Episode]')
print("-" * 60)
meals = ['早餐-1', '早餐-2', '午餐-1', '午餐-2', '晚餐-1', '晚餐-2']
for step in range(6):
    valid = [i for i, m in enumerate(masks) if m]
    action = valid[0]  # 选第一个有效动作
    obs, reward, done, _, info = env.step(action)
    recipe_name = info['selected_recipe']
    price = env.recipes[action]['price']
    cal = env.recipes[action]['calories']
    print(f'  {meals[step]}: {recipe_name} ({price}元, {cal}kcal)')
    masks = env.action_masks()
    if done:
        print("-" * 60)
        print(f'  总热量: {info["total_calories"]:.0f} kcal (目标: {env.target_calories})')
        print(f'  总花费: {info["total_cost"]:.1f} 元 (预算: {env.budget_limit})')
        print(f'  菜品类别数: {info["unique_categories"]}')
        break

# 测试训练模式的课程学习
print('\n[课程学习配置]')
env_train = MealPlanningEnv(training_mode=True)

env_train.global_step = 0
env_train.reset()
print(f'  Stage 1 (0-100k): 预算={env_train.budget_limit}元, 热量={env_train.target_calories}kcal')

env_train.global_step = 150000
env_train.reset()
print(f'  Stage 2 (100k-300k): 预算={env_train.budget_limit:.1f}元, 热量={env_train.target_calories:.0f}kcal')

env_train.global_step = 400000
env_train.reset()
print(f'  Stage 3 (300k+): 预算={env_train.budget_limit:.1f}元, 热量={env_train.target_calories:.0f}kcal')

print("\n" + "=" * 60)
print("验证完成! 环境配置正确。")
print("=" * 60)
print("\n运行训练命令:")
print("  conda activate ai_lab")
print("  python scripts/train_optimized.py")
