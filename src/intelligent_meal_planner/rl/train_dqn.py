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
from stable_baselines3.common.env_util import make_vec_env
from stable_baselines3.common.vec_env import VecNormalize
from stable_baselines3.common.callbacks import CheckpointCallback
from sb3_contrib.common.maskable.callbacks import MaskableEvalCallback as EvalCallback
from stable_baselines3.common.monitor import Monitor
from .environment import MealPlanningEnv


def mask_fn(env: MealPlanningEnv) -> list:
    return env.get_wrapper_attr("action_masks")()


def train_model(
    total_timesteps: int = 2000000,
    learning_rate: float = 0.0003, # Slightly higher LR for larger batch? Keep 0.0001 or user suggested 0.0003 in prompt? Prompt said 0.0003.
    batch_size: int = 512,
    gamma: float = 0.99,
    model_save_path: str = None,
    log_dir: str = None,
    n_envs: int = 16, 
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
    print("MaskablePPO High-Performance Training (Speed Optimized)")
    print("="*60)
    print(f"Configuration:")
    print(f"  Device:          RTX 4060 (CUDA)")
    print(f"  CPU Parallel:    {n_envs} Environments")
    print(f"  Total Timesteps: {total_timesteps}")
    print(f"  Learning Rate:   {learning_rate}")
    print(f"  Batch Size:      {batch_size}")
    print(f"  Gamma:           {gamma}")
    print(f"  Log Directory:   {log_dir}")
    print("="*60)
    
    
    # ---------------------------------------------------------
    # 1. & 2. Speed & Effectiveness Upgrade: VecEnv + Normalization
    # ---------------------------------------------------------
    
    # Define environment factory
    def make_env():
        # Note: Monitor is handled by make_vec_env's monitor_dir argument (it wraps SubprocVecEnv/DummyVecEnv with VecMonitor? 
        # Actually make_vec_env creates envs, wraps then in Monitor, then VecEnv. 
        # But we need ActionMasker. ActionMasker must be applied on the individual environment before VecEnv wrapping.
        env = MealPlanningEnv(
            target_calories=2000.0,
            target_protein=100.0,
            target_carbs=250.0,
            target_fat=65.0,
            budget_limit=120.0,
            disliked_tags=[],
            training_mode=True
        )
        env = ActionMasker(env, mask_fn)
        return env

    print(f"\n[1/4] Initializing Vectorized Environment (n_envs={n_envs})...")
    env = make_vec_env(
        make_env, 
        n_envs=n_envs, 
        monitor_dir=str(log_dir / "train")
    )
    
    print("       Applying VecNormalize...")
    env = VecNormalize(
        env,
        norm_obs=True,
        norm_reward=True,
        clip_obs=10.0,
        gamma=gamma
    )
    
    print("\n[2/4] Initializing Evaluation Environment...")
    # Evaluation Env (also vectorized/normalized)
    def make_eval_env():
         env = MealPlanningEnv(
            target_calories=2000.0,
            budget_limit=120.0,
            training_mode=False 
         )
         env = ActionMasker(env, mask_fn)
         return env

    eval_env = make_vec_env(make_eval_env, n_envs=1, monitor_dir=str(log_dir / "eval"))
    # Use VecNormalize for eval too, but with training=False to avoid polluting stats?
    # However, keeping training=True for eval env allows it to adapt to its own distribution (if separate).
    # Ideally should share stats, but passing the object is complex with make_vec_env.
    # We will use training=True for stability in this context, or load stats? 
    # Let's set training=True so it normalizes based on what it sees, ensuring inputs are in range.
    eval_env = VecNormalize(eval_env, norm_obs=True, norm_reward=False, clip_obs=10.0, gamma=gamma, training=True)
    
    print("\n[3/4] Building MaskablePPO Policy Network...")
    # policy_kwargs: 定义网络结构，使用的是 net_arch=[256, 256] 以重增强 Critic 能力
    policy_kwargs = dict(net_arch=[256, 256])
    
    # Calculate n_steps to keep total buffer size reasonable (e.g. ~4096 or 8192)
    # n_envs * n_steps = buffer_size
    # With 16 envs, n_steps=256 -> 4096 buffer
    steps_per_env = 4096 // n_envs
    
    model = MaskablePPO(
        "MlpPolicy",
        env,
        learning_rate=learning_rate,
        # PPO params
        n_steps=steps_per_env, 
        batch_size=batch_size,
        n_epochs=10,
        gamma=gamma,
        gae_lambda=0.95,
        clip_range=0.2,
        ent_coef=0.05, 
        policy_kwargs=policy_kwargs,
        verbose=1,
        tensorboard_log=str(log_dir / "tensorboard"),
        device="cuda" # Force GPU
    )
    
    # 创建回调函数
    checkpoint_callback = CheckpointCallback(
        save_freq=max(10000 // n_envs, 1), # Checkpoint freq in steps per env
        save_path=str(model_save_path / "checkpoints"),
        name_prefix="ppo_meal_planner", 
        save_replay_buffer=False, 
        save_vecnormalize=True, 
    )
    
    eval_callback = EvalCallback(
        eval_env,
        best_model_save_path=str(model_save_path),
        log_path=str(log_dir / "eval"),
        eval_freq=max(5000 // n_envs, 1),
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
        log_interval=10, 
        progress_bar=True,
    )
    
    # 保存最终模型
    final_model_path = model_save_path / "ppo_meal_planner_final.zip"
    model.save(str(final_model_path))
    # Save normalization stats explicitly as well
    env.save(str(model_save_path / "vec_normalize.pkl"))
    
    print("="*60)
    print(f"\nTraining Complete!")
    print(f"Model saved to: {final_model_path}")
    print(f"Normalization stats saved to: {model_save_path / 'vec_normalize.pkl'}")
    
    # 清理
    env.close()
    eval_env.close()
    
    return model


def test_model(model_path: str, n_episodes: int = 5, randomize: bool = False):
    """
    测试训练好的模型
    """
    print("="*60)
    print(f"测试模型 (随机化目标: {randomize})")
    print("="*60)
    
    # 加载模型
    try:
        model = MaskablePPO.load(model_path)
    except Exception as e:
        print(f"加载模型失败: {e}")
        return
    
    
    # Analyze model path to find stats
    model_path_obj = Path(model_path)
    # Check for stats in same dir or parent (e.g. if model is in checkpoints/)
    stats_path = model_path_obj.parent / "vec_normalize.pkl"
    if not stats_path.exists():
        stats_path = model_path_obj.parent.parent / "vec_normalize.pkl"
        
    print(f"Loading model from: {model_path}")
    if stats_path.exists():
        print(f"Found normalization stats: {stats_path}")
    else:
        print("Warning: No normalization stats found. Model might perform poorly if it expects normalized inputs.")

    # Create Test Env (Vectorized for compatibility with VecNormalize)
    def make_test_env():
         env = MealPlanningEnv(
            target_calories=2000.0,
            # 如果开启 randomize，则设为 training_mode=True (允许 reset 时随机)
            # 但要注意 env.train_mode 只是 flag，具体随机逻辑看 reset
            training_mode=randomize 
         )
         env = ActionMasker(env, mask_fn)
         return env
         
    env = make_vec_env(make_test_env, n_envs=1)
    
    # Load Normalization Stats if available
    if stats_path.exists():
        env = VecNormalize.load(str(stats_path), env)
        env.training = False # Don't update stats during test
        env.norm_reward = False # We want real rewards for logging
        
    total_rewards = []
    
    for episode in range(n_episodes):
        obs = env.reset() # VecEnv reset returns just obs
        # 如果是随机模式，我们可以打印一下当前的目标（需要 hack 一下访问内部 env）
        if randomize:
            # VecEnv -> get_attr -> list of values
            targets = env.get_attr("target_calories")
            budgets = env.get_attr("budget_limit")
            print(f"  [随机目标] 卡路里: {targets[0]:.0f}, 预算: {budgets[0]:.0f}")
        episode_reward = 0
        done = False
        
        print(f"\n第 {episode + 1} 回合:")
        
        while not done:
            # VecEnv observation is already (n_envs, features)
            # Action mask calculation for VecEnv?
            # ActionMasker in VecEnv puts masks in 'action_mask' key of info dict if using sb3-contrib wrappers?
            # Or we need to call env.env_method("action_masks")?
            # Actually, sb3-contrib MaskablePPO predict handles VecEnv automatically? 
            # predict(obs, action_masks=...)
            # We need to get masks manually for the single env.
            # access list of masks:
            action_masks = env.env_method("action_masks")[0]
            
            action, _states = model.predict(obs, action_masks=action_masks, deterministic=True)
            
            # VecEnv step
            obs, rewards, dones, infos = env.step(action)
            
            reward = rewards[0]
            done = dones[0]
            info = infos[0]
            
            episode_reward += reward
            
            if info.get('valid_action', False) or True: 
                name = info.get('selected_recipe', 'Unknown')
                print(f"  选择: {name} (Reward: {reward:.1f})")
        
        total_rewards.append(episode_reward)
        print(f"  总奖励: {episode_reward:.2f}")
    
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
    parser.add_argument(
        "--randomize",
        action="store_true",
        help="在测试模式下启用域随机化 (验证模型的泛化能力)"
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
        test_model(args.model_path, randomize=args.randomize)


if __name__ == "__main__":
    main()