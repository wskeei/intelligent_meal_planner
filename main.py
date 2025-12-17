"""
智能配餐系统 - 主入口

启动方式:
1. 启动后端 API:
   uv run python main.py api

2. 启动前端开发服务器:
   cd frontend && npm run dev

3. 训练 RL 模型:
   uv run python main.py train

4. 测试 Agent:
   uv run python main.py agent
"""

import sys
import subprocess
from pathlib import Path


def start_api():
    """启动 FastAPI 后端服务"""
    print("🚀 启动 FastAPI 后端服务...")
    print("   访问地址: http://localhost:8000")
    print("   API 文档: http://localhost:8000/docs")
    subprocess.run([
        sys.executable, "-m", "uvicorn",
        "src.intelligent_meal_planner.api.main:app",
        "--reload", "--host", "0.0.0.0", "--port", "8000"
    ])


def train_model():
    """训练 DQN 模型"""
    print("🎯 开始训练 DQN 模型...")
    from src.intelligent_meal_planner.rl.train_dqn import train_dqn
    train_dqn(total_timesteps=50000)


def test_agent():
    """测试 CrewAI Agent"""
    print("🤖 测试 CrewAI Agent...")
    from src.intelligent_meal_planner.agents.crew import MealPlanningCrew
    
    crew = MealPlanningCrew()
    result = crew.plan_meals(
        health_goal="balanced",
        calorie_target=2000,
        budget=100
    )
    print("\n配餐结果:")
    print(result)


def show_help():
    """显示帮助信息"""
    print(__doc__)
    print("可用命令:")
    print("  api    - 启动后端 API 服务")
    print("  train  - 训练 RL 模型")
    print("  agent  - 测试 CrewAI Agent")
    print("  help   - 显示此帮助信息")


def main():
    if len(sys.argv) < 2:
        show_help()
        return
    
    command = sys.argv[1].lower()
    
    commands = {
        "api": start_api,
        "train": train_model,
        "agent": test_agent,
        "help": show_help,
    }
    
    if command in commands:
        commands[command]()
    else:
        print(f"❌ 未知命令: {command}")
        show_help()


if __name__ == "__main__":
    main()
