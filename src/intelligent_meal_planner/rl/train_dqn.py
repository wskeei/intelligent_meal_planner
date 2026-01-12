"""
MaskablePPO 模型训练脚本 (优化版 v2)
使用 sb3-contrib 的 MaskablePPO 训练配餐模型 (支持动作屏蔽)

优化内容:
1. 课程学习 (Curriculum Learning) - 从简单到复杂
2. 熵系数调度 - 从高探索到低探索
3. 学习率调度 - 线性衰减
4. 优化的网络架构和超参数
5. 详细的训练监控
"""

import os
import argparse
import torch
from pathlib import Path
from typing import Callable
from sb3_contrib import MaskablePPO
from sb3_contrib.common.wrappers import ActionMasker
from stable_baselines3.common.env_util import make_vec_env
from stable_baselines3.common.vec_env import VecNormalize, VecEnv
from stable_baselines3.common.callbacks import BaseCallback, CheckpointCallback
from sb3_contrib.common.maskable.callbacks import MaskableEvalCallback as EvalCallback
from .environment import MealPlanningEnv


def mask_fn(env: MealPlanningEnv) -> list:
    return env.get_wrapper_attr("action_masks")()


# ========== 自定义回调函数 ==========

class CurriculumCallback(BaseCallback):
    """
    课程学习回调：更新环境的global_step，让环境知道当前训练进度
    """
    def __init__(self, verbose=0):
        super().__init__(verbose)

    def _on_step(self) -> bool:
        # 更新所有并行环境的global_step
        try:
            # 获取实际的vec_env (可能被VecNormalize包装)
            vec_env = self.training_env
            if hasattr(vec_env, 'venv'):  # VecNormalize包装
                vec_env = vec_env.venv

            # 设置每个子环境的global_step
            for i in range(vec_env.num_envs):
                vec_env.env_method('__setattr__', 'global_step', self.num_timesteps, indices=[i])
        except Exception as e:
            if self.verbose > 0:
                print(f"Warning: Could not update global_step: {e}")
        return True


class EntropyScheduler(BaseCallback):
    """
    熵系数调度器：从高探索逐渐降低到低探索
    """
    def __init__(self, initial_ent: float = 0.1, final_ent: float = 0.01,
                 schedule_timesteps: int = 300000, verbose=0):
        super().__init__(verbose)
        self.initial_ent = initial_ent
        self.final_ent = final_ent
        self.schedule_timesteps = schedule_timesteps

    def _on_step(self) -> bool:
        progress = min(1.0, self.num_timesteps / self.schedule_timesteps)
        new_ent = self.initial_ent - (self.initial_ent - self.final_ent) * progress

        # 更新模型的熵系数
        self.model.ent_coef = new_ent

        # 每10000步打印一次
        if self.num_timesteps % 10000 == 0 and self.verbose > 0:
            print(f"[EntropyScheduler] Step {self.num_timesteps}: ent_coef = {new_ent:.4f}")

        return True


class DetailedLoggingCallback(BaseCallback):
    """
    详细日志回调：记录更多训练指标
    """
    def __init__(self, log_freq: int = 1000, verbose=0):
        super().__init__(verbose)
        self.log_freq = log_freq
        self.episode_rewards = []
        self.episode_cal_errors = []

    def _on_step(self) -> bool:
        # 检查是否有episode结束
        if self.locals.get('dones') is not None:
            for i, done in enumerate(self.locals['dones']):
                if done and self.locals.get('infos') is not None:
                    info = self.locals['infos'][i]
                    if 'total_calories' in info:
                        # 记录卡路里误差等自定义指标
                        try:
                            vec_env = self.training_env
                            if hasattr(vec_env, 'venv'):
                                vec_env = vec_env.venv
                            target_cal = vec_env.get_attr('target_calories', [i])[0]
                            actual_cal = info['total_calories']
                            cal_error = abs(actual_cal - target_cal) / target_cal
                            self.logger.record('custom/cal_error_ratio', cal_error)

                            # 记录课程阶段
                            stage = vec_env.get_attr('curriculum_stage', [i])[0]
                            self.logger.record('custom/curriculum_stage', stage)
                        except:
                            pass

        return True


def linear_schedule(initial_value: float) -> Callable[[float], float]:
    """
    线性学习率调度器
    """
    def func(progress_remaining: float) -> float:
        return progress_remaining * initial_value
    return func


def train_model(
    total_timesteps: int = 500000,
    initial_learning_rate: float = 0.0003,
    batch_size: int = 128,
    gamma: float = 0.99,
    model_save_path: str = None,
    log_dir: str = None,
    n_envs: int = 8,
):
    """
    训练 MaskablePPO 模型 (优化版)
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

    # 检查CUDA
    device = "cuda" if torch.cuda.is_available() else "cpu"

    print("=" * 70)
    print("MaskablePPO Training (Optimized v2 with Curriculum Learning)")
    print("=" * 70)
    print(f"Configuration:")
    print(f"  Device:              {device.upper()}" +
          (f" ({torch.cuda.get_device_name(0)})" if device == "cuda" else ""))
    print(f"  Parallel Envs:       {n_envs}")
    print(f"  Total Timesteps:     {total_timesteps:,}")
    print(f"  Learning Rate:       {initial_learning_rate} (linear decay)")
    print(f"  Batch Size:          {batch_size}")
    print(f"  Gamma:               {gamma}")
    print(f"  Observation Space:   13 dimensions (expanded)")
    print(f"  Curriculum Learning: Stage 1 (0-100k) -> Stage 2 (100k-300k) -> Stage 3 (300k+)")
    print(f"  Entropy Schedule:    0.1 -> 0.01 over 300k steps")
    print(f"  Log Directory:       {log_dir}")
    print("=" * 70)

    # ========== 1. 创建训练环境 ==========
    def make_env():
        env = MealPlanningEnv(
            target_calories=2000.0,
            target_protein=100.0,
            target_carbs=250.0,
            target_fat=65.0,
            budget_limit=150.0,
            disliked_tags=[],
            training_mode=True
        )
        env = ActionMasker(env, mask_fn)
        return env

    print(f"\n[1/5] Initializing Vectorized Environment (n_envs={n_envs})...")
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
        clip_reward=10.0,
        gamma=gamma
    )

    # ========== 2. 创建评估环境 ==========
    print("\n[2/5] Initializing Evaluation Environment...")

    def make_eval_env():
        env = MealPlanningEnv(
            target_calories=2000.0,
            target_protein=100.0,
            target_carbs=250.0,
            target_fat=65.0,
            budget_limit=150.0,
            training_mode=False
        )
        env = ActionMasker(env, mask_fn)
        return env

    eval_env = make_vec_env(make_eval_env, n_envs=1, monitor_dir=str(log_dir / "eval"))
    eval_env = VecNormalize(
        eval_env,
        norm_obs=True,
        norm_reward=False,  # 评估时不normalize奖励，方便比较
        clip_obs=10.0,
        gamma=gamma,
        training=False  # 不更新统计
    )

    # ========== 3. 创建模型 ==========
    print("\n[3/5] Building MaskablePPO Policy Network...")

    # 优化的网络架构：分离的policy和value网络
    policy_kwargs = dict(
        net_arch=dict(
            pi=[256, 256, 128],  # Policy网络: 3层
            vf=[256, 256, 128]   # Value网络: 3层
        ),
        activation_fn=torch.nn.ReLU,
    )

    # 计算n_steps
    steps_per_env = 256  # 每个环境收集256步
    buffer_size = n_envs * steps_per_env  # 总buffer大小

    model = MaskablePPO(
        "MlpPolicy",
        env,
        learning_rate=linear_schedule(initial_learning_rate),
        n_steps=steps_per_env,
        batch_size=batch_size,
        n_epochs=15,  # 从10增加到15
        gamma=gamma,
        gae_lambda=0.95,
        clip_range=0.2,
        clip_range_vf=None,  # 不裁剪value function
        ent_coef=0.1,  # 初始熵系数（会被scheduler调整）
        vf_coef=0.5,
        max_grad_norm=0.5,
        policy_kwargs=policy_kwargs,
        verbose=1,
        tensorboard_log=str(log_dir / "tensorboard"),
        device=device
    )

    print(f"       Network architecture: pi={policy_kwargs['net_arch']['pi']}, vf={policy_kwargs['net_arch']['vf']}")
    print(f"       Buffer size: {buffer_size} ({n_envs} envs x {steps_per_env} steps)")

    # ========== 4. 创建回调函数 ==========
    print("\n[4/5] Setting up Callbacks...")

    # 检查点回调
    checkpoint_callback = CheckpointCallback(
        save_freq=max(10000 // n_envs, 1),
        save_path=str(model_save_path / "checkpoints"),
        name_prefix="ppo_meal_v2",
        save_replay_buffer=False,
        save_vecnormalize=True,
    )

    # 评估回调
    eval_callback = EvalCallback(
        eval_env,
        best_model_save_path=str(model_save_path),
        log_path=str(log_dir / "eval"),
        eval_freq=max(5000 // n_envs, 1),
        n_eval_episodes=10,
        deterministic=True,
        render=False,
    )

    # 课程学习回调
    curriculum_callback = CurriculumCallback(verbose=1)

    # 熵调度回调
    entropy_callback = EntropyScheduler(
        initial_ent=0.1,
        final_ent=0.01,
        schedule_timesteps=300000,
        verbose=1
    )

    # 详细日志回调
    logging_callback = DetailedLoggingCallback(log_freq=1000, verbose=0)

    callbacks = [
        checkpoint_callback,
        eval_callback,
        curriculum_callback,
        entropy_callback,
        logging_callback,
    ]

    # ========== 5. 开始训练 ==========
    print("\n[5/5] Starting Training Process...")
    print("       (Use 'tensorboard --logdir models/logs/tensorboard' for monitoring)")
    print(f"       (Progress bar below shows steps/{total_timesteps:,})")
    print("-" * 70)

    try:
        model.learn(
            total_timesteps=total_timesteps,
            callback=callbacks,
            log_interval=10,
            progress_bar=True,
        )
    except KeyboardInterrupt:
        print("\n\nTraining interrupted by user. Saving current model...")

    # ========== 保存最终模型 ==========
    final_model_path = model_save_path / "ppo_meal_v2_final.zip"
    model.save(str(final_model_path))
    env.save(str(model_save_path / "vec_normalize_v2.pkl"))

    print("=" * 70)
    print(f"\nTraining Complete!")
    print(f"Final model saved to: {final_model_path}")
    print(f"Normalization stats saved to: {model_save_path / 'vec_normalize_v2.pkl'}")
    print("=" * 70)

    # 清理
    env.close()
    eval_env.close()

    return model


def test_model(model_path: str, n_episodes: int = 5, randomize: bool = False):
    """
    测试训练好的模型
    """
    print("=" * 60)
    print(f"Testing Model (Randomize: {randomize})")
    print("=" * 60)

    # 加载模型
    try:
        model = MaskablePPO.load(model_path)
    except Exception as e:
        print(f"Failed to load model: {e}")
        return

    # 查找归一化统计文件
    model_path_obj = Path(model_path)
    stats_path = model_path_obj.parent / "vec_normalize_v2.pkl"
    if not stats_path.exists():
        stats_path = model_path_obj.parent / "vec_normalize.pkl"
    if not stats_path.exists():
        stats_path = model_path_obj.parent.parent / "vec_normalize_v2.pkl"

    print(f"Model: {model_path}")
    if stats_path.exists():
        print(f"Normalization stats: {stats_path}")
    else:
        print("Warning: No normalization stats found.")

    # 创建测试环境
    def make_test_env():
        env = MealPlanningEnv(
            target_calories=2000.0,
            target_protein=100.0,
            target_carbs=250.0,
            target_fat=65.0,
            budget_limit=150.0,
            training_mode=randomize
        )
        env = ActionMasker(env, mask_fn)
        return env

    env = make_vec_env(make_test_env, n_envs=1)

    # 加载归一化统计
    if stats_path.exists():
        env = VecNormalize.load(str(stats_path), env)
        env.training = False
        env.norm_reward = False

    total_rewards = []
    total_cal_errors = []

    for episode in range(n_episodes):
        obs = env.reset()

        # 获取当前目标
        target_cal = env.get_attr("target_calories")[0]
        budget = env.get_attr("budget_limit")[0]

        print(f"\n{'='*50}")
        print(f"Episode {episode + 1}: Target {target_cal:.0f} kcal, Budget ¥{budget:.0f}")
        print("-" * 50)

        episode_reward = 0
        done = False

        while not done:
            action_masks = env.env_method("action_masks")[0]
            action, _states = model.predict(obs, action_masks=action_masks, deterministic=True)
            obs, rewards, dones, infos = env.step(action)

            reward = rewards[0]
            done = dones[0]
            info = infos[0]
            episode_reward += reward

            recipe_name = info.get('selected_recipe', 'Unknown')
            step = info.get('step', '?')
            print(f"  Step {step}: {recipe_name} (r={reward:.2f})")

        # Episode结束统计
        final_cal = info.get('total_calories', 0)
        cal_error = abs(final_cal - target_cal) / target_cal * 100
        total_rewards.append(episode_reward)
        total_cal_errors.append(cal_error)

        print(f"\nResult: Total Reward = {episode_reward:.2f}")
        print(f"        Calories: {final_cal:.0f} / {target_cal:.0f} (Error: {cal_error:.1f}%)")
        print(f"        Cost: ¥{info.get('total_cost', 0):.1f}")

    # 总结
    avg_reward = sum(total_rewards) / len(total_rewards)
    avg_cal_error = sum(total_cal_errors) / len(total_cal_errors)

    print(f"\n{'='*50}")
    print(f"Summary over {n_episodes} episodes:")
    print(f"  Average Reward: {avg_reward:.2f}")
    print(f"  Average Calorie Error: {avg_cal_error:.1f}%")
    print("=" * 50)

    env.close()


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="Train or test MaskablePPO meal planning model")
    parser.add_argument(
        "--mode",
        type=str,
        choices=["train", "test"],
        default="train",
        help="Mode: train or test"
    )
    parser.add_argument(
        "--timesteps",
        type=int,
        default=500000,
        help="Total training timesteps (default: 500000)"
    )
    parser.add_argument(
        "--model-path",
        type=str,
        default=None,
        help="Model path (required for test mode)"
    )
    parser.add_argument(
        "--save-path",
        type=str,
        default=None,
        help="Model save directory"
    )
    parser.add_argument(
        "--randomize",
        action="store_true",
        help="Enable domain randomization in test mode"
    )
    parser.add_argument(
        "--n-envs",
        type=int,
        default=8,
        help="Number of parallel environments (default: 8)"
    )

    args = parser.parse_args()

    if args.mode == "train":
        train_model(
            total_timesteps=args.timesteps,
            model_save_path=args.save_path,
            n_envs=args.n_envs,
        )
    elif args.mode == "test":
        if args.model_path is None:
            print("Error: --model-path is required for test mode")
            return
        test_model(args.model_path, randomize=args.randomize)


if __name__ == "__main__":
    main()
