"""
智能配餐系统 - 主入口

启动方式:
1. 启动后端 API:
   uv run python main.py api

2. 启动前端开发服务器:
   cd frontend && npm run dev

3. 训练 RL 模型:
   uv run python main.py train

4. 查看旧 agent 入口的废弃提示:
   uv run python main.py agent
"""

import sys
import subprocess
from pathlib import Path


def start_api():
    """启动 FastAPI 后端服务"""
    print("启动 FastAPI 后端服务...")
    print("   访问地址: http://localhost:8000")
    print("   API 文档: http://localhost:8000/docs")
    subprocess.run([
        sys.executable, "-m", "uvicorn",
        "src.intelligent_meal_planner.api.main:app",
        "--reload", "--host", "0.0.0.0", "--port", "8000"
    ])


def train_model():
    """训练 DQN 模型"""
    print("开始训练 DQN 模型...")
    from src.intelligent_meal_planner.rl.train_dqn import train_dqn
    train_dqn(total_timesteps=50000)


def test_agent():
    """保留旧命令名，但不再提供单轮 CrewAI 运行入口。"""
    print("`main.py agent` 已废弃。")
    print("   运行时配餐已经迁移到对话式会话编排流程。")
    print("   请启动 API：uv run python main.py api")
    print("   然后在前端访问 /meal-plan 使用营养师对话配餐。")


def show_help():
    """显示帮助信息"""
    print(__doc__)
    print("可用命令:")
    print("  api    - 启动后端 API 服务")
    print("  train  - 训练 RL 模型")
    print("  agent  - 已废弃，保留为兼容提示")
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
        print(f"未知命令: {command}")
        show_help()


if __name__ == "__main__":
    main()
