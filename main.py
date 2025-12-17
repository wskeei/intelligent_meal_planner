"""
智能配餐系统 - 主入口

使用方法：
    # 启动 Streamlit 前端
    uv run streamlit run src/intelligent_meal_planner/app.py
    
    # 启动 FastAPI 后端
    uv run uvicorn intelligent_meal_planner.api.main:app --reload
    
    # 命令行快速配餐
    uv run python main.py
"""

import sys
import argparse


def run_streamlit():
    """启动 Streamlit 前端"""
    import subprocess
    subprocess.run([sys.executable, "-m", "streamlit", "run", 
                   "src/intelligent_meal_planner/app.py"])


def run_api():
    """启动 FastAPI 后端"""
    import uvicorn
    uvicorn.run("intelligent_meal_planner.api.main:app", 
                host="0.0.0.0", port=8000, reload=True)


def run_quick_plan(calories=2000, protein=100, carbs=250, fat=60, budget=50):
    """命令行快速配餐"""
    print("=" * 60)
    print("🍽️  智能配餐系统 - 快速配餐")
    print("=" * 60)
    
    try:
        from src.intelligent_meal_planner.tools.rl_model_tool import create_rl_model_tool
        from src.intelligent_meal_planner.tools.recipe_database_tool import recipe_db_tool
        
        print(f"\n📊 营养目标: {calories}kcal | 蛋白质{protein}g | 碳水{carbs}g | 脂肪{fat}g")
        print(f"💰 预算上限: ¥{budget}")
        print("\n⏳ 正在生成配餐方案...\n")
        
        tool = create_rl_model_tool()
        result = tool._run(
            target_calories=calories,
            target_protein=protein,
            target_carbs=carbs,
            target_fat=fat,
            max_budget=budget
        )
        
        import json
        data = json.loads(result)
        
        # 显示结果
        print("=" * 60)
        print("📋 今日配餐方案")
        print("=" * 60)
        
        meal_plan = data.get('meal_plan', {})
        meal_names = {'breakfast': '🌅 早餐', 'lunch': '☀️ 午餐', 'dinner': '🌙 晚餐'}
        
        for meal, recipe_id in meal_plan.items():
            print(f"\n{meal_names.get(meal, meal)}:")
            print(recipe_db_tool._run(recipe_ids=[recipe_id]))
        
        # 显示汇总
        metrics = data.get('metrics', {})
        print("\n" + "=" * 60)
        print("📊 营养汇总")
        print("=" * 60)
        print(f"总卡路里: {metrics.get('total_calories', 0):.0f} kcal ({metrics.get('calories_achievement', 0):.1f}% 达成)")
        print(f"总蛋白质: {metrics.get('total_protein', 0):.1f} g ({metrics.get('protein_achievement', 0):.1f}% 达成)")
        print(f"总碳水: {metrics.get('total_carbs', 0):.1f} g")
        print(f"总脂肪: {metrics.get('total_fat', 0):.1f} g")
        print(f"总花费: ¥{metrics.get('total_cost', 0):.1f} ({metrics.get('budget_usage', 0):.1f}% 预算)")
        
    except FileNotFoundError:
        print("❌ 错误: 模型文件未找到")
        print("请先运行训练: uv run python -m intelligent_meal_planner.rl.train_dqn --mode train")
    except Exception as e:
        print(f"❌ 错误: {e}")


def main():
    parser = argparse.ArgumentParser(description="智能配餐系统")
    parser.add_argument("--mode", choices=["web", "api", "plan"], default="plan",
                       help="运行模式: web(Streamlit), api(FastAPI), plan(命令行配餐)")
    parser.add_argument("--calories", type=int, default=2000, help="目标卡路里")
    parser.add_argument("--protein", type=int, default=100, help="目标蛋白质(g)")
    parser.add_argument("--carbs", type=int, default=250, help="目标碳水(g)")
    parser.add_argument("--fat", type=int, default=60, help="目标脂肪(g)")
    parser.add_argument("--budget", type=float, default=50, help="预算上限(元)")
    
    args = parser.parse_args()
    
    if args.mode == "web":
        run_streamlit()
    elif args.mode == "api":
        run_api()
    else:
        run_quick_plan(args.calories, args.protein, args.carbs, args.fat, args.budget)


if __name__ == "__main__":
    main()
