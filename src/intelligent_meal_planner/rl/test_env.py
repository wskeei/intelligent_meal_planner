"""
测试配餐环境
验证环境是否正常工作
"""

import sys
import io

# 设置标准输出为 UTF-8 编码，避免 Windows 控制台乱码
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from .environment import MealPlanningEnv


def test_environment():
    """测试环境基本功能"""
    print("="*60)
    print("测试配餐环境")
    print("="*60)
    
    # 创建环境
    env = MealPlanningEnv(
        target_calories=2000.0,
        target_protein=100.0,
        target_carbs=250.0,
        target_fat=65.0,
        budget_limit=60.0,
        disliked_tags=["重口味"],  # 设置忌口标签
    )
    
    print(f"\n环境信息:")
    print(f"  观察空间: {env.observation_space}")
    print(f"  动作空间: {env.action_space}")
    print(f"  可用菜品数量: {len(env.recipes)}")
    
    # 重置环境
    obs, info = env.reset()
    print(f"\n初始状态: {obs}")
    
    # 测试一个回合
    print("\n开始测试回合...")
    episode_reward = 0
    done = False
    step = 0
    
    while not done:
        step += 1
        
        # 获取当前餐次的有效动作
        valid_actions = env.get_valid_actions()
        print(f"\n步骤 {step}: 当前餐次 {env.meal_types[env.current_meal_idx]}")
        print(f"  有效动作数量: {len(valid_actions)}")
        
        # 随机选择一个有效动作
        if len(valid_actions) > 0:
            import random
            action = random.choice(valid_actions)
            
            # 执行动作
            obs, reward, terminated, truncated, info = env.step(action)
            episode_reward += reward
            done = terminated or truncated
            
            if info.get('valid_action', False):
                print(f"  选择菜品: {info['selected_recipe']}")
                print(f"  当前花费: {info['total_cost']:.2f}元")
                print(f"  当前卡路里: {info['total_calories']:.1f}")
            else:
                print(f"  错误: {info.get('error', '未知错误')}")
        else:
            print("  没有有效动作！")
            break
    
    print(f"\n回合结束:")
    print(f"  总奖励: {episode_reward:.2f}")
    
    # 渲染最终状态
    env.render()
    
    # 显示营养目标达成情况
    print(f"\n营养目标对比:")
    print(f"  卡路里: {env.total_calories:.1f} / {env.target_calories:.1f} "
          f"(差异: {abs(env.total_calories - env.target_calories):.1f})")
    print(f"  蛋白质: {env.total_protein:.1f}g / {env.target_protein:.1f}g "
          f"(差异: {abs(env.total_protein - env.target_protein):.1f}g)")
    print(f"  碳水: {env.total_carbs:.1f}g / {env.target_carbs:.1f}g "
          f"(差异: {abs(env.total_carbs - env.target_carbs):.1f}g)")
    print(f"  脂肪: {env.total_fat:.1f}g / {env.target_fat:.1f}g "
          f"(差异: {abs(env.total_fat - env.target_fat):.1f}g)")
    print(f"  预算: {env.total_cost:.1f}元 / {env.budget_limit:.1f}元")
    
    env.close()
    
    print("\n测试完成！")
    print("="*60)


if __name__ == "__main__":
    test_environment()