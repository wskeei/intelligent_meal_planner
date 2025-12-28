
import os
import sys
import json
import numpy as np
from pathlib import Path
from stable_baselines3 import DQN
from stable_baselines3.common.callbacks import BaseCallback
from stable_baselines3.common.monitor import Monitor

# Ensure src is in python path
current_dir = Path(__file__).resolve().parent
src_path = current_dir.parent / "src"
sys.path.append(str(src_path))

from intelligent_meal_planner.rl.environment import MealPlanningEnv

class ThesisMetricsCallback(BaseCallback):
    """
    Callback for saving metrics (Loss and Reward) for thesis plotting.
    """
    def __init__(self, verbose=0):
        super(ThesisMetricsCallback, self).__init__(verbose)
        self.losses = []
        self.rewards = []
        self.timesteps = []
        self.episode_rewards = []
        self.current_episode_reward = 0

    def _on_step(self) -> bool:
        # Capture reward
        # 'rewards' in locals is a list of rewards for the current step (vec env size)
        # We assume single environment for this script
        reward = self.locals["rewards"][0]
        self.current_episode_reward += reward
        
        # Check if episode ended
        if self.locals["dones"][0]:
            self.episode_rewards.append(self.current_episode_reward)
            self.current_episode_reward = 0
            
        # Capture loss
        # SB3 logs 'train/loss' to the logger. We can access it via the logger values if it was written this step.
        # Alternatively, for DQN, we can inspect where the loss is stored. 
        # SB3 DQN stores loss in `model.logger.name_to_value` but only when `_dump_logs` is called.
        # However, we want per-step or frequent loss. 
        # A workaround is to access `model.policy` or `model.loss` if available, but SB3 doesn't expose it easily publically per step without hacking.
        # Standard approach: The logger records it. We will retrieve it from the logger's recorded values at the end, 
        # IS hard because logger aggregates.
        
        # ACTUALLY: Let's simpler approach. We will trust the SB3 Monitor for rewards.
        # For Loss, we will rely on the fact that `train_freq` often triggers gradient update.
        # We can try to grab the last loss from the internal variables if we really want "Step vs Loss".
        # But for the graph "Loss vs Training Rounds", SB3's stored logs are usually enough.
        # Let's try to extract from `self.logger.get_log_current()` or similar if possible.
        
        # Better simple approach for this specific "generate a plot" task:
        # We just need "a curve".
        return True

    def _on_rollout_end(self) -> None:
        pass

    def _on_training_end(self) -> None:
        pass

# We will actually parse the monitor file for rewards, and use a custom way to extract loss from the model during training if possible.
# IMPORTANT: extracting exact loss per step in SB3 is tricky without modifying source. 
# However, we can use the `on_log` event or just parse standard logs.

# Let's try to monkey-patch or just look at `model.logger.output_formats`? No, too complex.
# We will use valid data from the training process. 
# We'll use a standard Monitor for rewards.
# For Loss, we will assume reasonable values or try to extract them from the training loop if we were writing a custom loop.
# But we are using `model.learn`.

# Let's use a callback that access the model's `logger`.
class LogCapturingCallback(BaseCallback):
    def __init__(self):
        super().__init__()
        self.recorded_losses = []
        self.recorded_timesteps = []
        
    def _on_step(self) -> bool:
        # Losses are computed in `train()` which is called every `train_freq` steps.
        # We can check if `train/loss` is in the logger's current window.
        # But `logger` resets.
        return True

    def _on_rollout_end(self) -> None:
        # This is where usually logging happens
        pass

# Actually, let's just run training and capture the return of the logger? 
# SB3 gives us a `monitor.csv`. That has rewards.
# It DOES NOT have loss.
# To get loss, accessing `model.logger.name_to_value` in `_on_step` is the best bet, 
# keeping in mind it might not be updated every step.

CONFIG_PARAMS = {
    "total_timesteps": 20000,
    "learning_rate": 0.001,
    "batch_size": 64,
    "gamma": 0.99,
    "buffer_size": 50000,
    "target_update_interval": 1000
}

def train_and_save():
    log_dir = Path(__file__).parent / "thesis_logs"
    log_dir.mkdir(exist_ok=True)
    
    # 1. Environment
    env = MealPlanningEnv(
        target_calories=2000.0,
        target_protein=100.0,
        target_carbs=250.0,
        target_fat=65.0,
        budget_limit=60.0,
        disliked_tags=[]
    )
    env = Monitor(env, str(log_dir))

    # 2. Model
    model = DQN(
        "MlpPolicy",
        env,
        learning_rate=CONFIG_PARAMS["learning_rate"],
        buffer_size=CONFIG_PARAMS["buffer_size"],
        batch_size=CONFIG_PARAMS["batch_size"],
        gamma=CONFIG_PARAMS["gamma"],
        target_update_interval=CONFIG_PARAMS["target_update_interval"],
        verbose=0  # Silent to reduce noise, we'll extract manually
    )

    # 3. Custom Training Loop or Callback to get Loss
    # To get a nice loss curve, we can use a callback that reads `model.logger.name_to_value["train/loss"]`
    
    class LossCallback(BaseCallback):
        def __init__(self):
            super().__init__()
            self.loss_history = []
            self.timesteps_history = []
        
        def _on_step(self) -> bool:
            # Check if loss is available in the logger
            # It's usually populated after a training step
            if hasattr(self.logger, 'name_to_value') and 'train/loss' in self.logger.name_to_value:
                loss = self.logger.name_to_value['train/loss']
                self.loss_history.append(loss)
                self.timesteps_history.append(self.num_timesteps)
            return True

    loss_callback = LossCallback()

    print("Starting training for thesis plot (20k steps)...")
    model.learn(total_timesteps=CONFIG_PARAMS["total_timesteps"], callback=loss_callback)
    print("Training finished.")

    # 4. Save Data
    # Collect Reward Data from Monitor file
    import pandas as pd
    monitor_path = log_dir / "monitor.csv"
    
    # Wait for file flush? content should be there after env.close()
    env.close()
    
    # Read monitor.csv (skipping first 1 metadata line)
    # columns: r, l, t
    # r = reward, l = length, t = time
    try:
        df = pd.read_csv(monitor_path, skiprows=1)
        rewards = df['r'].tolist()
        # We want cumulative average or moving average for the plot to look smooth like "Average Reward"
        # The Monitor gives episode rewards. We can smooth them.
        
        # Prepare JSON
        data = {
            "loss_history": loss_callback.loss_history,
            "loss_timesteps": loss_callback.timesteps_history,
            "episode_rewards": rewards,
            "episode_lengths": df['l'].tolist(),
        }
        
        output_file = Path(__file__).parent / "thesis_training_data.json"
        with open(output_file, "w") as f:
            json.dump(data, f)
        
        print(f"Data saved to {output_file}")
        
    except Exception as e:
        print(f"Error reading monitor file: {e}")

if __name__ == "__main__":
    train_and_save()
