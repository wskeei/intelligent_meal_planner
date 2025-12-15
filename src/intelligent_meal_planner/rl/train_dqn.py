"""
DQN 模型训练脚本
使用 Stable-Baselines3 训练配餐模型
"""

import os
import argparse
from pathlib import Path
from stable_baselines3 import DQN
from stable_baselines3.common.callbacks import CheckpointCallback, EvalCallback
from stable_baselines3.common.monitor import Monitor
from .environment import MealPlanningEnv


def train_dqn(
    total_timesteps: int = 100000,
    learning_rate: float = 0.0001,
    buffer_size: int = 50000,
    batch_size: int = 32,
    gamma: float = 0.99,
    target_update_interval: int = 1000,
    model_save_path: str = None,
    log_dir: str = None,
):
    """
    训练 DQN 模型
    
    Args:
        total_timesteps: 总训练步数
        learning_rate: 学习率
        buffer_size: 经验回放缓冲区大小
        batch_size: 批次大小
        gamma: 折扣因子
        target_update_interval: 目标网络更新间隔
        model_save_path: 模型保存路径
        log_dir: 日志目录
    """
    
    # 设置默认路径
    if model_save_path is None:
        model_save_path = Path(__file__).parent.parent.parent.parent / "models"
    else:
        model_save_path = Path(model_save_path)
    
    model_save_path.mkdir(parents=True, exist_ok=True)
    
    if log_dir is None:
        log_dir = model_save_path / "logs"
    else:
        log_dir = Path(log_dir)
    
    log_dir.mkdir(parents=True, exist_ok=True)
    
    print("="*60)
    print("开始训练 DQN 配餐模型")
    print("="*60)
    print(f"训练参数:")
    print(f"  总步数: {total_timesteps}")
    print(f"  学习率: {learning_rate}")
    print(f"  缓冲区大小: {buffer_size}")
    print(f"  批次大小: {batch_size}")
    print(f"  折扣因子: {gamma}")
    print(f"  模型保存路径: {model_save_path}")
    print(f"  日志目录: {log_dir}")
    print("="*60)
    
    # 创建训练环境
    env = MealPlanningEnv(
        target_calories=2000.0,
        target_protein=100.0,
        target_carbs=250.0,
        target_fat=65.0,
        budget_limit=60.0,
        disliked_tags=[],  # 训练时不设置忌口
    )
    
    # 使用 Monitor 包装环境以记录统计信息
    env = Monitor(env, str(log_dir / "train"))
    
    # 创建评估环境
    eval_env = MealPlanningEnv(
        target_calories=2000.0,
        target_protein=100.0,
        target_carbs=250.0,
        target_fat=65.0,
        budget_limit=60.0,
        disliked_tags=[],
    )
    eval_env = Monitor(eval_env, str(log_dir / "eval"))
    
    # 创建 DQN 模型
    model = DQN(
        "MlpPolicy",  # 多层感知机策略
        env,
        learning_rate=learning_rate,
        buffer_size=buffer_size,
        batch_size=batch_size,
        gamma=gamma,
        target_update_interval=target_update_interval,
        exploration_fraction=0.3,  # 探索阶段占比
        exploration_initial_eps=1.0,  # 初始探索率
        exploration_final_eps=0.05,  # 最终探索率
        verbose=1,
        tensorboard_log=str(log_dir / "tensorboard"),
    )
    
    # 创建回调函数
    checkpoint_callback = CheckpointCallback(
        save_freq=10000,
        save_path=str(model_save_path / "checkpoints"),
        name_prefix="dqn_meal_planner",
        save_replay_buffer=True,
        save_vecnormalize=True,
    )
    
    eval_callback = EvalCallback(
        eval_env,
        best_model_save_path=str(model_save_path),
        log_path=str(log_dir / "eval"),
        eval_freq=5000,
        n_eval_episodes=10,
        deterministic=True,
        render=False,
    )
    
    # 开始训练
    print("\n开始训练...")
    model.learn(
        total_timesteps=total_timesteps,
        callback=[checkpoint_callback, eval_callback],
        log_interval=100,
        progress_bar=True,
    )
    
    # 保存最终模型
    final_model_path = model_save_path / "dqn_meal_planner_final.zip"
    model.save(str(final_model_path))
    print(f"\n模型已保存到: {final_model_path}")
    
    # 清理
    env.close()
    eval_env.close()
    
    print("\n训练完成！")
    print("="*60)
    
    return model


def test_model(model_path: str, n_episodes: int = 5):
    """
    测试训练好的模型
    
    Args:
        model_path: 模型文件路径
        n_episodes: 测试回合数
    """
    print("="*60)
    print("测试模型")
    print("="*60)
    
    # 加载模型
    model = DQN.load(model_path)
    
    # 创建测试环境
    env = MealPlanningEnv(
        target_calories=2000.0,
        target_protein=100.0,
        target_carbs=250.0,
        target_fat=65.0,
        budget_limit=60.0,
        disliked_tags=[],
    )
    
    total_rewards = []
    
    for episode in range(n_episodes):
        obs, info = env.reset()
        episode_reward = 0
        done = False
        
        print(f"\n第 {episode + 1} 回合:")
        
        while not done:
            # 使用模型预测动作
            action, _states = model.predict(obs, deterministic=True)
            obs, reward, terminated, truncated, info = env.step(action)
            episode_reward += reward
            done = terminated or truncated
            
            if info.get('valid_action', False):
                print(f"  选择: {info['selected_recipe']}")
        
        total_rewards.append(episode_reward)
        print(f"  总奖励: {episode_reward:.2f}")
        env.render()
    
    avg_reward = sum(total_rewards) / len(total_rewards)
    print(f"\n平均奖励: {avg_reward:.2f}")
    print("="*60)
    
    env.close()


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="训练或测试 DQN 配餐模型")
    parser.add_argument(
        "--mode",
        type=str,
        choices=["train", "test"],
        default="train",
        help="运行模式: train 或 test"
    )
    parser.add_argument(
        "--timesteps",
        type=int,
        default=100000,
        help="训练总步数"
    )
    parser.add_argument(
        "--model-path",
        type=str,
        default=None,
        help="模型路径（测试模式下必需）"
    )
    parser.add_argument(
        "--save-path",
        type=str,
        default=None,
        help="模型保存路径"
    )
    
    args = parser.parse_args()
    
    if args.mode == "train":
        train_dqn(
            total_timesteps=args.timesteps,
            model_save_path=args.save_path,
        )
    elif args.mode == "test":
        if args.model_path is None:
            print("错误: 测试模式需要提供 --model-path 参数")
            return
        test_model(args.model_path)


if __name__ == "__main__":
    main()