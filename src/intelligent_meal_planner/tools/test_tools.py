"""
工具测试脚本 - 测试 RecipeDatabaseTool 和 RLModelTool

运行命令：
    uv run python -m intelligent_meal_planner.tools.test_tools
"""

import sys
import io
from pathlib import Path

# 设置UTF-8编码输出，解决Windows控制台中文显示问题
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from intelligent_meal_planner.tools.recipe_database_tool import RecipeDatabaseTool
from intelligent_meal_planner.tools.rl_model_tool import create_rl_model_tool


def test_recipe_database_tool():
    """测试菜品数据库工具"""
    print("=" * 60)
    print("测试 1: 菜品数据库工具")
    print("=" * 60)
    
    # 创建工具实例
    tool = RecipeDatabaseTool()
    
    # 测试1: 查询特定ID的菜品
    print("\n【测试1】查询菜品ID 1, 5, 10:")
    result = tool._run(recipe_ids=[1, 5, 10])
    print(result)
    
    # 测试2: 查询早餐菜品
    print("\n【测试2】查询所有早餐菜品（限制3个）:")
    result = tool._run(meal_type="breakfast", limit=3)
    print(result)
    
    # 测试3: 价格筛选
    print("\n【测试3】查询价格在10-20元之间的菜品（限制3个）:")
    result = tool._run(min_price=10.0, max_price=20.0, limit=3)
    print(result)
    
    # 测试4: 标签筛选
    print("\n【测试4】查询高蛋白菜品（限制3个）:")
    result = tool._run(tags=["高蛋白"], limit=3)
    print(result)
    
    # 测试5: 获取营养汇总
    print("\n【测试5】获取菜品1, 5, 10的营养汇总:")
    summary = tool.get_recipe_summary([1, 5, 10])
    print(f"总热量: {summary['calories']} kcal")
    print(f"总蛋白质: {summary['protein']} g")
    print(f"总碳水: {summary['carbs']} g")
    print(f"总脂肪: {summary['fat']} g")
    print(f"总花费: ¥{summary['price']}")
    print(f"菜品: {[r['name'] for r in summary['recipes']]}")
    
    print("\n[OK] 菜品数据库工具测试完成")


def test_rl_model_tool():
    """测试强化学习模型工具"""
    print("\n" + "=" * 60)
    print("测试 2: 强化学习模型工具")
    print("=" * 60)
    
    try:
        # 创建工具实例
        tool = create_rl_model_tool()
        
        # 测试: 生成配餐方案
        print("\n【测试】生成配餐方案（目标: 增肌）:")
        print("  目标卡路里: 2500 kcal")
        print("  目标蛋白质: 150 g")
        print("  目标碳水: 300 g")
        print("  目标脂肪: 70 g")
        print("  预算: 60 元")
        
        result = tool._run(
            target_calories=2500,
            target_protein=150,
            target_carbs=300,
            target_fat=70,
            max_budget=60.0,
            disliked_ingredients=["辣椒"]
        )
        
        print("\n生成的配餐方案:")
        print(result)
        
        print("\n[OK] 强化学习模型工具测试完成")
        
    except FileNotFoundError as e:
        print(f"\n[警告] 模型文件未找到: {e}")
        print("   请先训练模型，或确认模型路径正确")
    except Exception as e:
        print(f"\n[错误] 测试失败: {e}")
        import traceback
        traceback.print_exc()


def main():
    """主测试函数"""
    print("\n" + "=" * 60)
    print("开始测试工具类")
    print("=" * 60)
    
    # 测试菜品数据库工具
    test_recipe_database_tool()
    
    # 测试强化学习模型工具
    test_rl_model_tool()
    
    print("\n" + "=" * 60)
    print("所有测试完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()