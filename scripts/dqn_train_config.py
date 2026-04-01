"""
DQN 训练配置 — AI Agent 可修改的文件

这是 DQN autoresearch 循环中 AI agent 唯一可以修改的文件。
所有超参数、网络结构、训练循环细节都在这里。

使用方式:
    from dqn_train_config import train
    agent = train(timesteps=50000)
"""

import sys
from pathlib import Path

import numpy as np
import torch

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from intelligent_meal_planner.rl.environment import MealPlanningEnv
from intelligent_meal_planner.rl.dqn import MaskableDQNAgent


# ============ 超参数配置 (AI Agent 修改区) ============

PRICE_SCALE = 1.0
BUDGET_SCALE = 1.5

CUSTOM_RECIPES = [
    # --- 便宜午/晚餐 ---
    {
        "name": "家常豆腐", "calories": 280, "protein": 15, "carbs": 12, "fat": 18,
        "price": 5, "meal_type": ["lunch", "dinner"], "category": "Tofu", "tags": ["cheap"],
    },
    {
        "name": "番茄蛋汤", "calories": 180, "protein": 10, "carbs": 15, "fat": 8,
        "price": 4, "meal_type": ["lunch", "dinner"], "category": "Soup", "tags": ["cheap"],
    },
    {
        "name": "辣子鸡丁", "calories": 400, "protein": 28, "carbs": 12, "fat": 25,
        "price": 7, "meal_type": ["lunch", "dinner"], "category": "Poultry", "tags": ["cheap"],
    },
    {
        "name": "肉末粉条", "calories": 380, "protein": 18, "carbs": 30, "fat": 20,
        "price": 6, "meal_type": ["lunch", "dinner"], "category": "Meat", "tags": ["cheap"],
    },
    {
        "name": "香煎带鱼", "calories": 350, "protein": 22, "carbs": 5, "fat": 25,
        "price": 8, "meal_type": ["lunch", "dinner"], "category": "Seafood", "tags": ["cheap"],
    },
    # --- 酮友好 ---
    {
        "name": "生酮煎蛋", "calories": 320, "protein": 18, "carbs": 2, "fat": 26,
        "price": 5, "meal_type": ["breakfast"], "category": "Breakfast", "tags": ["keto"],
    },
    {
        "name": "五花肉烧白菜", "calories": 480, "protein": 20, "carbs": 8, "fat": 40,
        "price": 10, "meal_type": ["lunch", "dinner"], "category": "Meat", "tags": ["keto"],
    },
    {
        "name": "清蒸鸡腿", "calories": 380, "protein": 30, "carbs": 3, "fat": 26,
        "price": 9, "meal_type": ["lunch", "dinner"], "category": "Poultry", "tags": ["keto"],
    },
    # --- 高热量 ---
    {
        "name": "大份蛋炒饭", "calories": 600, "protein": 15, "carbs": 80, "fat": 22,
        "price": 8, "meal_type": ["lunch", "dinner"], "category": "Staple", "tags": ["bulk"],
    },
    {
        "name": "肥牛盖饭", "calories": 700, "protein": 28, "carbs": 70, "fat": 30,
        "price": 14, "meal_type": ["lunch", "dinner"], "category": "Meat", "tags": ["bulk"],
    },
]

# 网络结构
HIDDEN_DIMS = [256, 256, 128]

# 优化
LEARNING_RATE = 1e-4
LEARNING_RATE_END = 1e-5
GAMMA = 0.99
BATCH_SIZE = 512
GRAD_CLIP = 10.0

# 经验回放
BUFFER_SIZE = 100000
MIN_BUFFER_SIZE = 10000

# 训练频率
TRAIN_FREQ = 2
TARGET_UPDATE_FREQ = 500
N_ENVS = 8

# 优先经验回放 (PER)
PER_ALPHA = 0.6
PER_BETA_START = 0.4
PER_BETA_END = 1.0

# 设备
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"


def get_epsilon_schedule(timesteps: int):
    """Epsilon 衰减策略 — 与课程学习阶段对齐。

    AI agent 可以修改此函数来调整探索策略。
    返回: list of (start_step, end_step, start_eps, end_eps) 元组
    """
    return [
        (0, max(1, timesteps // 10), 1.0, 0.3),
        (max(1, timesteps // 10), max(2, timesteps * 2 // 5), 0.3, 0.05),
        (max(2, timesteps * 2 // 5), timesteps, 0.05, 0.01),
    ]


def get_config(timesteps: int) -> dict:
    """构建完整的 DQN 配置字典。

    AI agent 可以修改上面的常量，也可以直接修改此函数。
    """
    return {
        "hidden_dims": HIDDEN_DIMS,
        "gamma": GAMMA,
        "learning_rate": LEARNING_RATE,
        "learning_rate_end": LEARNING_RATE_END,
        "batch_size": BATCH_SIZE,
        "train_freq": TRAIN_FREQ,
        "target_update_freq": TARGET_UPDATE_FREQ,
        "grad_clip": GRAD_CLIP,
        "buffer_size": BUFFER_SIZE,
        "min_buffer_size": min(MIN_BUFFER_SIZE, timesteps // 2),
        "epsilon_schedule": get_epsilon_schedule(timesteps),
        "per_alpha": PER_ALPHA,
        "per_beta_start": PER_BETA_START,
        "per_beta_end": PER_BETA_END,
        "per_beta_steps": max(1, timesteps * 4 // 5),
        "n_envs": N_ENVS,
        "device": DEVICE,
        "total_timesteps": timesteps,
        "price_scale": PRICE_SCALE,
        "budget_scale": BUDGET_SCALE,
        "custom_recipes": CUSTOM_RECIPES,
    }


def train(timesteps: int) -> MaskableDQNAgent:
    """训练 DQN agent 并返回。

    AI agent 可以修改训练循环的任何细节。

    Args:
        timesteps: 训练总步数。

    Returns:
        训练完成的 MaskableDQNAgent。
    """
    config = get_config(timesteps)
    n_envs = config["n_envs"]
    price_scale = config["price_scale"]
    custom_recipes = config.get("custom_recipes", [])

    envs = [
        MealPlanningEnv(training_mode=True, price_scale=price_scale, custom_recipes=custom_recipes)
        for _ in range(n_envs)
    ]
    agent = MaskableDQNAgent(state_dim=13, action_dim=300, config=config)

    obs_list = [env.reset()[0] for env in envs]
    mask_list = [env.action_masks() for env in envs]

    global_step = 0
    while global_step < timesteps:
        for env in envs:
            env.global_step = global_step * 10

        actions = [
            agent.select_action(obs_list[i], mask_list[i], global_step)
            for i in range(n_envs)
        ]

        for i in range(n_envs):
            next_obs, reward, terminated, truncated, info = envs[i].step(actions[i])
            done = terminated or truncated
            next_mask = envs[i].action_masks()

            agent.store_transition(
                obs_list[i], actions[i], reward, next_obs, done,
                mask_list[i], next_mask,
            )

            if done:
                obs_list[i], _ = envs[i].reset()
                mask_list[i] = envs[i].action_masks()
            else:
                obs_list[i] = next_obs
                mask_list[i] = next_mask

        global_step += n_envs

        if global_step % config["train_freq"] == 0:
            agent.train_step_fn()
            agent.train_step_fn()  # UTD ratio = 2

    return agent
