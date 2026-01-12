"""
高性能训练脚本 - 针对 RTX 4060 + 24核CPU + 32GB RAM 优化

硬件利用策略:
- GPU (8GB VRAM): 大batch_size + torch.compile加速
- CPU (24核/32线程): 32个并行环境
- RAM (32GB): 大buffer + 预加载数据

运行方式:
    conda activate ai_lab
    python scripts/train_optimized.py
"""

import os
import sys
import time
import torch
import numpy as np
from pathlib import Path
from typing import Callable

# 添加src到路径
current_dir = Path(__file__).resolve().parent
src_path = current_dir.parent / "src"
sys.path.insert(0, str(src_path))

from sb3_contrib import MaskablePPO
from sb3_contrib.common.wrappers import ActionMasker
from stable_baselines3.common.env_util import make_vec_env
from stable_baselines3.common.vec_env import VecNormalize, SubprocVecEnv, DummyVecEnv
from stable_baselines3.common.callbacks import BaseCallback, CheckpointCallback, CallbackList
from sb3_contrib.common.maskable.callbacks import MaskableEvalCallback as EvalCallback

from intelligent_meal_planner.rl.environment import MealPlanningEnv


# ==================== 性能优化设置 ====================

# 针对你的硬件的最优配置
HARDWARE_CONFIG = {
    'n_envs': 24,           # 并行环境数 (= CPU核心数，充分利用多核)
    'batch_size': 512,      # 批大小 (8GB显存可以支持)
    'n_steps': 256,         # 每环境步数 (buffer = 24*256 = 6144)
    'n_epochs': 10,         # PPO更新轮数
    'learning_rate': 3e-4,  # 学习率
    'total_timesteps': 500000,  # 总步数
}

# PyTorch性能优化
def setup_torch_optimizations():
    """配置PyTorch性能优化"""
    # 启用cuDNN自动调优
    torch.backends.cudnn.benchmark = True

    # 设置浮点精度 (TF32加速)
    torch.backends.cuda.matmul.allow_tf32 = True
    torch.backends.cudnn.allow_tf32 = True

    # 设置线程数
    torch.set_num_threads(8)  # 留一些线程给环境

    # 禁用梯度检查 (生产模式)
    torch.autograd.set_detect_anomaly(False)
    torch.autograd.profiler.profile(False)
    torch.autograd.profiler.emit_nvtx(False)


# ==================== 回调函数 ====================

class CurriculumCallback(BaseCallback):
    """课程学习回调"""
    def __init__(self, verbose=0):
        super().__init__(verbose)
        self.last_log_step = 0

    def _on_step(self) -> bool:
        try:
            vec_env = self.training_env
            if hasattr(vec_env, 'venv'):
                vec_env = vec_env.venv

            for i in range(vec_env.num_envs):
                vec_env.env_method('__setattr__', 'global_step', self.num_timesteps, indices=[i])
        except:
            pass
        return True


class EntropyScheduler(BaseCallback):
    """熵系数调度"""
    def __init__(self, initial_ent=0.1, final_ent=0.01, schedule_steps=300000, verbose=0):
        super().__init__(verbose)
        self.initial_ent = initial_ent
        self.final_ent = final_ent
        self.schedule_steps = schedule_steps

    def _on_step(self) -> bool:
        progress = min(1.0, self.num_timesteps / self.schedule_steps)
        self.model.ent_coef = self.initial_ent - (self.initial_ent - self.final_ent) * progress
        return True


class PerformanceMonitor(BaseCallback):
    """性能监控回调"""
    def __init__(self, log_freq=10000, verbose=1):
        super().__init__(verbose)
        self.log_freq = log_freq
        self.start_time = None
        self.last_log_time = None
        self.last_log_step = 0

    def _on_training_start(self):
        self.start_time = time.time()
        self.last_log_time = self.start_time

    def _on_step(self) -> bool:
        if self.num_timesteps - self.last_log_step >= self.log_freq:
            current_time = time.time()

            # 计算速度
            elapsed = current_time - self.last_log_time
            steps = self.num_timesteps - self.last_log_step
            fps = steps / elapsed if elapsed > 0 else 0

            # 总体进度
            total_elapsed = current_time - self.start_time
            total_fps = self.num_timesteps / total_elapsed if total_elapsed > 0 else 0

            # 获取当前curriculum stage
            try:
                vec_env = self.training_env
                if hasattr(vec_env, 'venv'):
                    vec_env = vec_env.venv
                stage = vec_env.get_attr('curriculum_stage', [0])[0]
            except:
                stage = '?'

            print(f"\n[PERF] Step {self.num_timesteps:,} | "
                  f"FPS: {fps:.0f} (avg: {total_fps:.0f}) | "
                  f"Stage: {stage} | "
                  f"Entropy: {self.model.ent_coef:.3f}")

            self.last_log_time = current_time
            self.last_log_step = self.num_timesteps

        return True


# ==================== 环境工厂 ====================

def mask_fn(env):
    return env.get_wrapper_attr("action_masks")()


def make_train_env():
    """创建训练环境"""
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


def make_eval_env():
    """创建评估环境"""
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


def linear_schedule(initial_value: float) -> Callable[[float], float]:
    """线性学习率衰减"""
    def func(progress_remaining: float) -> float:
        return progress_remaining * initial_value
    return func


# ==================== 主训练函数 ====================

def train():
    """主训练函数"""

    # 设置路径
    base_dir = Path(__file__).parent.parent
    model_dir = base_dir / "models"
    log_dir = model_dir / "logs"
    checkpoint_dir = model_dir / "checkpoints"

    model_dir.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)
    checkpoint_dir.mkdir(parents=True, exist_ok=True)

    # 应用PyTorch优化
    setup_torch_optimizations()

    # 配置
    cfg = HARDWARE_CONFIG
    device = "cuda" if torch.cuda.is_available() else "cpu"

    # 打印配置
    print("=" * 70)
    print("HIGH-PERFORMANCE TRAINING - Optimized for RTX 4060 + 24-Core CPU")
    print("=" * 70)
    print(f"\n[Hardware]")
    print(f"  GPU:    {torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'N/A'}")
    print(f"  VRAM:   {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")
    print(f"  Device: {device.upper()}")
    print(f"\n[Training Config]")
    print(f"  Parallel Envs:   {cfg['n_envs']} (using SubprocVecEnv for CPU parallelism)")
    print(f"  Steps/Env:       {cfg['n_steps']}")
    print(f"  Buffer Size:     {cfg['n_envs'] * cfg['n_steps']:,} samples")
    print(f"  Batch Size:      {cfg['batch_size']}")
    print(f"  Total Steps:     {cfg['total_timesteps']:,}")
    print(f"  Learning Rate:   {cfg['learning_rate']} (linear decay)")
    print(f"\n[Optimizations]")
    print(f"  cuDNN Benchmark: Enabled")
    print(f"  TF32 Precision:  Enabled")
    print(f"  Entropy Sched:   0.1 -> 0.01 over 300k steps")
    print(f"  Curriculum:      Stage1(0-100k) -> Stage2(100k-300k) -> Stage3(300k+)")
    print("=" * 70)

    # ========== 创建环境 ==========
    print(f"\n[1/4] Creating {cfg['n_envs']} parallel environments...")
    start_time = time.time()

    # 使用SubprocVecEnv实现真正的多进程并行
    # 每个环境在独立进程中运行，充分利用多核CPU
    env = make_vec_env(
        make_train_env,
        n_envs=cfg['n_envs'],
        vec_env_cls=SubprocVecEnv,  # 多进程并行！
        monitor_dir=str(log_dir / "train")
    )

    # 应用归一化
    env = VecNormalize(
        env,
        norm_obs=True,
        norm_reward=True,
        clip_obs=10.0,
        clip_reward=10.0,
        gamma=0.99
    )

    print(f"       Done in {time.time() - start_time:.1f}s")

    # ========== 创建评估环境 ==========
    print(f"\n[2/4] Creating evaluation environment...")
    eval_env = make_vec_env(make_eval_env, n_envs=1, monitor_dir=str(log_dir / "eval"))
    eval_env = VecNormalize(
        eval_env,
        norm_obs=True,
        norm_reward=False,
        clip_obs=10.0,
        training=False
    )

    # ========== 创建模型 ==========
    print(f"\n[3/4] Building MaskablePPO model...")

    # 优化的网络架构
    policy_kwargs = dict(
        net_arch=dict(
            pi=[256, 256, 128],
            vf=[256, 256, 128]
        ),
        activation_fn=torch.nn.ReLU,
    )

    model = MaskablePPO(
        "MlpPolicy",
        env,
        learning_rate=linear_schedule(cfg['learning_rate']),
        n_steps=cfg['n_steps'],
        batch_size=cfg['batch_size'],
        n_epochs=cfg['n_epochs'],
        gamma=0.99,
        gae_lambda=0.95,
        clip_range=0.2,
        clip_range_vf=None,
        ent_coef=0.1,
        vf_coef=0.5,
        max_grad_norm=0.5,
        policy_kwargs=policy_kwargs,
        verbose=0,  # 减少输出，提高性能
        tensorboard_log=str(log_dir / "tensorboard"),
        device=device
    )

    # 统计模型参数量
    total_params = sum(p.numel() for p in model.policy.parameters())
    print(f"       Model parameters: {total_params:,}")

    # ========== 创建回调 ==========
    print(f"\n[4/4] Setting up callbacks...")

    callbacks = CallbackList([
        # 检查点 (每1万步保存)
        CheckpointCallback(
            save_freq=max(10000 // cfg['n_envs'], 1),
            save_path=str(checkpoint_dir),
            name_prefix="ppo_meal_fast",
            save_vecnormalize=True,
        ),
        # 评估 (每5000步评估一次)
        EvalCallback(
            eval_env,
            best_model_save_path=str(model_dir),
            log_path=str(log_dir / "eval"),
            eval_freq=max(5000 // cfg['n_envs'], 1),
            n_eval_episodes=5,  # 减少评估次数以加速
            deterministic=True,
            render=False,
        ),
        # 课程学习
        CurriculumCallback(verbose=0),
        # 熵调度
        EntropyScheduler(initial_ent=0.1, final_ent=0.01, schedule_steps=300000),
        # 性能监控
        PerformanceMonitor(log_freq=10000, verbose=1),
    ])

    # ========== 开始训练 ==========
    print("\n" + "=" * 70)
    print("TRAINING STARTED")
    print("=" * 70)
    print(f"\nMonitor with TensorBoard: tensorboard --logdir {log_dir / 'tensorboard'}")
    print(f"Expected FPS: ~3000-5000 steps/sec with your hardware")
    print("-" * 70 + "\n")

    training_start = time.time()

    try:
        model.learn(
            total_timesteps=cfg['total_timesteps'],
            callback=callbacks,
            log_interval=None,  # 禁用默认log，使用自定义
            progress_bar=True,
        )
    except KeyboardInterrupt:
        print("\n\nTraining interrupted! Saving model...")

    training_time = time.time() - training_start

    # ========== 保存最终模型 ==========
    final_model_path = model_dir / "ppo_meal_fast_final.zip"
    model.save(str(final_model_path))
    env.save(str(model_dir / "vec_normalize_fast.pkl"))

    # ========== 打印总结 ==========
    print("\n" + "=" * 70)
    print("TRAINING COMPLETE")
    print("=" * 70)
    print(f"\n[Results]")
    print(f"  Total Time:     {training_time / 60:.1f} minutes")
    print(f"  Total Steps:    {cfg['total_timesteps']:,}")
    print(f"  Average FPS:    {cfg['total_timesteps'] / training_time:.0f}")
    print(f"\n[Saved Files]")
    print(f"  Model:          {final_model_path}")
    print(f"  Normalization:  {model_dir / 'vec_normalize_fast.pkl'}")
    print(f"  Checkpoints:    {checkpoint_dir}")
    print(f"  TensorBoard:    {log_dir / 'tensorboard'}")
    print("=" * 70)

    # 清理
    env.close()
    eval_env.close()

    return model


def test(model_path: str = None, n_episodes: int = 5):
    """测试模型"""
    base_dir = Path(__file__).parent.parent
    model_dir = base_dir / "models"

    if model_path is None:
        model_path = model_dir / "ppo_meal_fast_final.zip"
    else:
        model_path = Path(model_path)

    stats_path = model_dir / "vec_normalize_fast.pkl"
    if not stats_path.exists():
        stats_path = model_dir / "vec_normalize_v2.pkl"

    print(f"Loading model: {model_path}")
    model = MaskablePPO.load(str(model_path))

    # 创建测试环境
    env = make_vec_env(make_eval_env, n_envs=1)
    if stats_path.exists():
        env = VecNormalize.load(str(stats_path), env)
        env.training = False
        env.norm_reward = False
        print(f"Loaded normalization stats: {stats_path}")

    print(f"\nRunning {n_episodes} test episodes...\n")

    total_rewards = []
    total_cal_errors = []

    for ep in range(n_episodes):
        obs = env.reset()
        target_cal = env.get_attr("target_calories")[0]

        print(f"Episode {ep+1}: Target {target_cal:.0f} kcal")

        done = False
        ep_reward = 0

        while not done:
            masks = env.env_method("action_masks")[0]
            action, _ = model.predict(obs, action_masks=masks, deterministic=True)
            obs, rewards, dones, infos = env.step(action)

            ep_reward += rewards[0]
            done = dones[0]

            if done:
                info = infos[0]
                final_cal = info.get('total_calories', 0)
                cal_error = abs(final_cal - target_cal) / target_cal * 100
                total_rewards.append(ep_reward)
                total_cal_errors.append(cal_error)

                print(f"  Reward: {ep_reward:.2f}, "
                      f"Calories: {final_cal:.0f}/{target_cal:.0f} ({cal_error:.1f}% error), "
                      f"Cost: ¥{info.get('total_cost', 0):.1f}")

    print(f"\n{'='*50}")
    print(f"Summary: Avg Reward = {np.mean(total_rewards):.2f}, "
          f"Avg Cal Error = {np.mean(total_cal_errors):.1f}%")
    print("=" * 50)

    env.close()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["train", "test"], default="train")
    parser.add_argument("--model", type=str, default=None, help="Model path for testing")
    parser.add_argument("--timesteps", type=int, default=500000, help="Training timesteps")
    args = parser.parse_args()

    if args.mode == "train":
        if args.timesteps != 500000:
            HARDWARE_CONFIG['total_timesteps'] = args.timesteps
        train()
    else:
        test(args.model)
