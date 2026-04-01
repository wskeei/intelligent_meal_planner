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

# 价格 & 预算缩放 — 调控配餐问题的可行域
# PRICE_SCALE: 缩放所有菜品价格 (0.5=半价, 1.0=原价, 2.0=双倍)
# BUDGET_SCALE: 缩放所有预算限制 (0.5=紧缩, 1.0=原始, 2.0=宽松)
# 范围: 0.3 ~ 3.0，中国正常饮食建议 PRICE_SCALE * avg_price ∈ [5, 35] 元
PRICE_SCALE = 1.0
BUDGET_SCALE = 1.0

# 自定义菜品 — AI agent 可在此添加新菜品（最多 150 道）
# 每道菜品必须通过 recipe_validator 验证，不合法的会被自动过滤
# 格式示例:
# CUSTOM_RECIPES = [
#     {
#         "name": "鸡胸肉沙拉",
#         "calories": 350, "protein": 35, "carbs": 15, "fat": 12,
#         "price": 18, "meal_type": ["lunch", "dinner"],
#         "category": "Poultry", "tags": ["healthy"],
#     },
# ]
CUSTOM_RECIPES = []

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
TRAIN_FREQ = 4
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
