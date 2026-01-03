"""
DQN/PPO 模型训练脚本
使用 sb3-contrib 的 MaskablePPO 训练配餐模型 (支持动作屏蔽)
注：原 plans 中提到了 MaskableDQN，但 sb3-contrib 仅包含 MaskablePPO，故使用 PPO 替代。
"""

import os
import argparse
from pathlib import Path
from sb3_contrib import MaskablePPO
from sb3_contrib.common.wrappers import ActionMasker
from stable_baselines3.common.callbacks import CheckpointCallback
from sb3_contrib.common.maskable.callbacks import MaskableEvalCallback as EvalCallback
from stable_baselines3.common.monitor import Monitor
from .environment import MealPlanningEnv


def mask_fn(env: MealPlanningEnv) -> list:
    return env.get_wrapper_attr("action_masks")()


def train_model(
    total_timesteps: int = 2000000,
    learning_rate: float = 0.0001, # Decreased for stability
    batch_size: int = 64,
    gamma: float = 0.99,
    model_save_path: str = None,
    log_dir: str = None,
):
    """
    训练 MaskablePPO 模型
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
    print("MaskablePPO Model Training (Optimization Version)")
    print("="*60)
    print(f"Configuration:")
    print(f"  Total Timesteps: {total_timesteps}")
    print(f"  Learning Rate:   {learning_rate}")
    print(f"  Batch Size:      {batch_size}")
    print(f"  Gamma:           {gamma}")
    print(f"  Model Path:      {model_save_path}")
    print(f"  Log Directory:   {log_dir}")
    print("="*60)
    
    print("\n[1/4] Initializing Training Environment...")
    env = MealPlanningEnv(
        target_calories=2000.0,
        target_protein=100.0,
        target_carbs=250.0,
        target_fat=65.0,
        budget_limit=120.0,
        disliked_tags=[],
    )
    
    # 使用 Monitor 包装环境以记录统计信息
    env = Monitor(env, str(log_dir / "train"))
    
    # 包装环境以支持动作屏蔽
    env = ActionMasker(env, mask_fn)
    
    print("\n[2/4] Initializing Evaluation Environment...")
    # 创建评估环境
    eval_env = MealPlanningEnv(
        target_calories=2000.0,
        target_protein=100.0,
        target_carbs=250.0,
        target_fat=65.0,
        budget_limit=120.0,
        disliked_tags=[],
    )
    eval_env = Monitor(eval_env, str(log_dir / "eval"))
    # 评估环境也需要支持动作屏蔽
    eval_env = ActionMasker(eval_env, mask_fn)
    
    print("\n[3/4] Building MaskablePPO Policy Network...")
    # 创建 MaskablePPO 模型
    # policy_kwargs: 定义网络结构，使用的是 net_arch=[256, 256] 以增强 Critic 能力 (解决 Explained Variance 低的问题)
    policy_kwargs = dict(net_arch=[256, 256])
    
    model = MaskablePPO(
        "MlpPolicy",
        env,
        learning_rate=learning_rate,
        # PPO params
        n_steps=2048,
        batch_size=batch_size,
        n_epochs=10,
        gamma=gamma,
        gae_lambda=0.95,
        clip_range=0.2,
        ent_coef=0.01,
        policy_kwargs=policy_kwargs,
        verbose=1,
        tensorboard_log=str(log_dir / "tensorboard"),
    )
    
    # 创建回调函数
    checkpoint_callback = CheckpointCallback(
        save_freq=10000,
        save_path=str(model_save_path / "checkpoints"),
        name_prefix="ppo_meal_planner", # Changed prefix
        save_replay_buffer=False, # PPO is on-policy, no replay buffer
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
    print("\n[4/4] Starting Training Process...")
    print("       (Check Tensorboard for real-time metrics)")
    print(f"       (Progress bar below shows steps/{total_timesteps})")
    model.learn(
        total_timesteps=total_timesteps,
        callback=[checkpoint_callback, eval_callback],
        log_interval=10, # PPO updates less frequently than DQN, so log every update (approx)
        progress_bar=True,
    )
    
    # 保存最终模型
    final_model_path = model_save_path / "ppo_meal_planner_final.zip"
    model.save(str(final_model_path))
    print("="*60)
    print(f"\nTraining Complete!")
    print(f"Model saved to: {final_model_path}")

    # Fallback for explicit steps file
    expected_path = model_save_path / "checkpoints" / "ppo_meal_planner_final.zip"
    
    # 清理
    env.close()
    eval_env.close()
    
    print("\n训练完成！")
    print("="*60)
    
    return model


def test_model(model_path: str, n_episodes: int = 5):
    """
    测试训练好的模型
    """
    print("="*60)
    print("测试模型")
    print("="*60)
    
    # 加载模型
    try:
        model = MaskablePPO.load(model_path)
    except Exception as e:
        print(f"加载模型失败: {e}")
        return
    
    # 创建测试环境
    env = MealPlanningEnv(
        target_calories=2000.0,
        target_protein=100.0,
        target_carbs=250.0,
        target_fat=65.0,
        budget_limit=120.0,
        disliked_tags=[],
    )
    # 不一定要 wrap，但为了 predict 中用到 action_masks
    env = ActionMasker(env, mask_fn)
    
    total_rewards = []
    
    for episode in range(n_episodes):
        obs, info = env.reset()
        episode_reward = 0
        done = False
        
        print(f"\n第 {episode + 1} 回合:")
        
        while not done:
            # 使用模型预测动作 (需要显式传递 masks 或使用 ActionMasker 包装的正确调用方式)
            action_masks = env.action_masks()
            action, _states = model.predict(obs, action_masks=action_masks, deterministic=True)
            obs, reward, terminated, truncated, info = env.step(action)
            episode_reward += reward
            done = terminated or truncated
            
            if info.get('valid_action', False) or True: # Info check
                name = info.get('selected_recipe', 'Unknown')
                print(f"  选择: {name} (Reward: {reward:.1f})")
        
        total_rewards.append(episode_reward)
        print(f"  总奖励: {episode_reward:.2f}")
        # env.render() # Removed render call to reduce spam or if env doesn't support it well in loop
    
    avg_reward = sum(total_rewards) / len(total_rewards)
    print(f"\n平均奖励: {avg_reward:.2f}")
    print("="*60)
    
    env.close()


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="训练或测试 MaskablePPO 配餐模型")
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
        default=2000000,
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
        train_model(
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