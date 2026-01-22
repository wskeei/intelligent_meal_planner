"""
DQN 训练脚本 - 带动作掩码的 Dueling Double DQN

使用方法:
    python scripts/train_dqn_maskable.py
    python scripts/train_dqn_maskable.py --timesteps 300000
    python scripts/train_dqn_maskable.py --mode test
"""

import sys
import os
import argparse
import time
from pathlib import Path
from datetime import datetime

import numpy as np
import torch
from torch.utils.tensorboard import SummaryWriter

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from intelligent_meal_planner.rl.environment import MealPlanningEnv
from intelligent_meal_planner.rl.dqn import MaskableDQNAgent, EpsilonScheduler


# ============ 配置 ============
DQN_CONFIG = {
    # 网络
    'hidden_dims': [256, 256, 128],

    # 训练
    'gamma': 0.99,
    'learning_rate': 1e-4,
    'learning_rate_end': 1e-5,
    'batch_size': 256,
    'train_freq': 4,
    'target_update_freq': 1000,
    'grad_clip': 10.0,

    # 经验回放
    'buffer_size': 100000,
    'min_buffer_size': 10000,

    # 探索 (与课程学习阶段对齐)
    'epsilon_schedule': [
        (0, 100_000, 1.0, 0.3),
        (100_000, 300_000, 0.3, 0.1),
        (300_000, 500_000, 0.1, 0.02),
    ],

    # PER
    'per_alpha': 0.6,
    'per_beta_start': 0.4,
    'per_beta_end': 1.0,
    'per_beta_steps': 400000,

    # 硬件
    'n_envs': 8,
    'device': 'cuda' if torch.cuda.is_available() else 'cpu',
    'total_timesteps': 500000,
}

# 路径配置
MODEL_DIR = project_root / "models"
LOG_DIR = MODEL_DIR / "logs" / "tensorboard" / "dqn"
CHECKPOINT_DIR = MODEL_DIR / "checkpoints" / "dqn"


def make_env(training_mode: bool = True) -> MealPlanningEnv:
    """创建环境"""
    return MealPlanningEnv(training_mode=training_mode)


def train(total_timesteps: int = None):
    """训练 DQN 模型"""
    total_timesteps = total_timesteps or DQN_CONFIG['total_timesteps']
    n_envs = DQN_CONFIG['n_envs']

    print(f"=" * 60)
    print(f"DQN 训练开始")
    print(f"设备: {DQN_CONFIG['device']}")
    print(f"并行环境数: {n_envs}")
    print(f"总步数: {total_timesteps:,}")
    print(f"=" * 60)

    # 创建目录
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)

    # 创建环境
    envs = [make_env(training_mode=True) for _ in range(n_envs)]

    # 创建 Agent
    config = DQN_CONFIG.copy()
    config['total_timesteps'] = total_timesteps
    agent = MaskableDQNAgent(state_dim=13, action_dim=150, config=config)

    # TensorBoard
    run_name = f"dqn_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    writer = SummaryWriter(LOG_DIR / run_name)

    # 训练状态
    obs_list = [env.reset()[0] for env in envs]
    mask_list = [env.action_masks() for env in envs]
    episode_rewards = [0.0] * n_envs
    episode_lengths = [0] * n_envs

    # 统计
    total_episodes = 0
    recent_rewards = []
    best_reward = float('-inf')
    start_time = time.time()

    global_step = 0
    train_freq = DQN_CONFIG['train_freq']

    print(f"\n开始收集经验...")

    while global_step < total_timesteps:
        # 更新课程学习
        for env in envs:
            env.global_step = global_step

        # 选择动作
        actions = []
        for i in range(n_envs):
            action = agent.select_action(
                obs_list[i], mask_list[i], global_step
            )
            actions.append(action)

        # 执行动作
        for i in range(n_envs):
            next_obs, reward, terminated, truncated, info = envs[i].step(actions[i])
            done = terminated or truncated
            next_mask = envs[i].action_masks()

            # 存储经验
            agent.store_transition(
                obs_list[i], actions[i], reward, next_obs, done,
                mask_list[i], next_mask
            )

            episode_rewards[i] += reward
            episode_lengths[i] += 1

            if done:
                # Episode 结束
                total_episodes += 1
                recent_rewards.append(episode_rewards[i])
                if len(recent_rewards) > 100:
                    recent_rewards.pop(0)

                # 重置
                obs_list[i], _ = envs[i].reset()
                mask_list[i] = envs[i].action_masks()
                episode_rewards[i] = 0.0
                episode_lengths[i] = 0
            else:
                obs_list[i] = next_obs
                mask_list[i] = next_mask

        global_step += n_envs

        # 训练
        if global_step % train_freq == 0:
            metrics = agent.train_step_fn()

            if metrics and global_step % 1000 == 0:
                writer.add_scalar('train/loss', metrics['loss'], global_step)
                writer.add_scalar('train/q_mean', metrics['q_mean'], global_step)
                writer.add_scalar('train/learning_rate', metrics['learning_rate'], global_step)

        # 日志
        if global_step % 10000 == 0:
            elapsed = time.time() - start_time
            fps = global_step / elapsed
            epsilon = agent.epsilon_scheduler.get_epsilon(global_step)
            avg_reward = np.mean(recent_rewards) if recent_rewards else 0

            print(f"Step {global_step:>7,} | "
                  f"Episodes: {total_episodes:>5} | "
                  f"Avg Reward: {avg_reward:>7.2f} | "
                  f"Epsilon: {epsilon:.3f} | "
                  f"FPS: {fps:.0f}")

            writer.add_scalar('rollout/ep_reward_mean', avg_reward, global_step)
            writer.add_scalar('rollout/epsilon', epsilon, global_step)
            writer.add_scalar('time/fps', fps, global_step)

            # 保存最佳模型
            if avg_reward > best_reward and len(recent_rewards) >= 50:
                best_reward = avg_reward
                agent.save(MODEL_DIR / "dqn_meal_best.pt")
                print(f"  -> 保存最佳模型 (reward: {best_reward:.2f})")

        # 检查点
        if global_step % 50000 == 0:
            agent.save(CHECKPOINT_DIR / f"dqn_step_{global_step}.pt")

    # 保存最终模型
    agent.save(MODEL_DIR / "dqn_meal_final.pt")
    writer.close()

    print(f"\n训练完成!")
    print(f"最终平均奖励: {np.mean(recent_rewards):.2f}")
    print(f"模型保存至: {MODEL_DIR / 'dqn_meal_final.pt'}")


def test(model_path: str = None, n_episodes: int = 5):
    """测试模型"""
    model_path = model_path or (MODEL_DIR / "dqn_meal_final.pt")

    print(f"加载模型: {model_path}")
    agent = MaskableDQNAgent.from_pretrained(model_path)

    env = make_env(training_mode=False)
    rewards = []

    for ep in range(n_episodes):
        obs, _ = env.reset()
        mask = env.action_masks()
        total_reward = 0
        done = False

        print(f"\n=== Episode {ep + 1} ===")

        while not done:
            action = agent.select_action(obs, mask, step=500000, deterministic=True)
            obs, reward, terminated, truncated, info = env.step(action)
            done = terminated or truncated
            mask = env.action_masks()
            total_reward += reward

        rewards.append(total_reward)

        # 打印结果
        cal_error = abs(env.total_calories - env.target_calories) / env.target_calories * 100
        print(f"总奖励: {total_reward:.2f}")
        print(f"卡路里: {env.total_calories:.0f} / {env.target_calories:.0f} (误差: {cal_error:.1f}%)")
        print(f"花费: {env.total_cost:.1f} / {env.budget_limit:.1f} 元")
        print(f"选择的菜品: {len(env.selected_recipe_indices)} 道")

    print(f"\n平均奖励: {np.mean(rewards):.2f} ± {np.std(rewards):.2f}")


def main():
    parser = argparse.ArgumentParser(description='DQN 训练脚本')
    parser.add_argument('--mode', type=str, default='train', choices=['train', 'test'])
    parser.add_argument('--timesteps', type=int, default=500000)
    parser.add_argument('--model', type=str, default=None)
    args = parser.parse_args()

    if args.mode == 'train':
        train(total_timesteps=args.timesteps)
    else:
        test(model_path=args.model)


if __name__ == '__main__':
    main()
