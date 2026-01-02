"""
Windows GPU Training Script for Intelligent Meal Planner
Optimized for CUDA usage and robust saving on Windows.
"""

import os
import sys
import torch
from pathlib import Path
from stable_baselines3 import DQN
from stable_baselines3.common.callbacks import CheckpointCallback, EvalCallback
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.env_util import make_vec_env

# Ensure src is in python path
current_dir = Path(__file__).resolve().parent
src_path = current_dir.parent / "src"
sys.path.append(str(src_path))

from intelligent_meal_planner.rl.environment import MealPlanningEnv

def train():
    # 1. Setup Paths
    base_dir = Path(__file__).parent.parent
    log_dir = base_dir / "models" / "logs"
    model_dir = base_dir / "models" / "saved"
    
    log_dir.mkdir(parents=True, exist_ok=True)
    model_dir.mkdir(parents=True, exist_ok=True)
    
    # 2. Check Device
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Training on device: {device.upper()}")
    if device == "cuda":
        print(f"GPU: {torch.cuda.get_device_name(0)}")
        
    # 3. Create Environment
    # Wrap in Monitor for logging
    env = MealPlanningEnv()
    env = Monitor(env, str(log_dir))
    
    # 4. Define Model (DQN)
    # Using larger buffer and network for more complex 9-step episodes
    policy_kwargs = dict(net_arch=[256, 256])
    
    model = DQN(
        "MlpPolicy",
        env,
        learning_rate=1e-4,
        buffer_size=100000, 
        learning_starts=1000,
        batch_size=128,
        gamma=0.99,
        train_freq=4,
        gradient_steps=1,
        target_update_interval=1000,
        exploration_fraction=0.3,
        exploration_final_eps=0.05,
        policy_kwargs=policy_kwargs,
        verbose=1,
        tensorboard_log=str(log_dir),
        device=device
    )
    
    # 5. Callbacks
    # Save a checkpoint every 10k steps
    checkpoint_callback = CheckpointCallback(
        save_freq=10000,
        save_path=str(model_dir),
        name_prefix="dqn_meal_planner"
    )
    
    # 6. Train
    total_timesteps = 200000 # Increased for better convergence with complex environment
    print(f"Starting training for {total_timesteps} timesteps...")
    
    try:
        model.learn(
            total_timesteps=total_timesteps, 
            callback=checkpoint_callback,
            progress_bar=True
        )
        print("Training completed successfully.")
    except Exception as e:
        print(f"Training interrupted: {e}")
    finally:
        # Save final model
        final_path = model_dir / "dqn_final"
        model.save(str(final_path))
        print(f"Final model saved to {final_path}")

if __name__ == "__main__":
    train()
