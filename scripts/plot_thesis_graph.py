
import json
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pathlib import Path

# Set font to support Chinese characters if available, otherwise fallback
from matplotlib.font_manager import FontProperties

def plot_thesis_graph():
    data_path = Path(__file__).parent / "thesis_training_data.json"
    if not data_path.exists():
        print(f"Data file not found: {data_path}")
        return

    with open(data_path, 'r') as f:
        data = json.load(f)

    losses = data.get("loss_history", [])
    rewards = data.get("episode_rewards", [])
    
    # Smooth data using pandas as requested
    # Loss smoothing
    if losses:
        smoothed_losses = pd.Series(losses).rolling(window=max(1, len(losses)//100), min_periods=1).mean()
    else:
        smoothed_losses = []
        
    # Reward smoothing
    if rewards:
        # Window size 15 as requested/suggested
        smoothed_rewards = pd.Series(rewards).rolling(window=15, min_periods=1).mean()
    else:
        smoothed_rewards = []
    
    # Create plot
    fig, ax1 = plt.subplots(figsize=(10, 6))

    # Plot Loss (Left Axis)
    color = 'tab:blue'
    ax1.set_xlabel('Training Steps', fontsize=12)
    
    loss_timesteps = data.get("loss_timesteps", [])
    if len(loss_timesteps) == len(losses):
        x_loss = loss_timesteps
    else:
        x_loss = range(len(losses))
        
    ax1.set_ylabel('Loss (MSE)', color=color, fontsize=12)
    ax1.plot(x_loss, smoothed_losses, color=color, linewidth=2, label='Loss')
    ax1.tick_params(axis='y', labelcolor=color)
    ax1.grid(True, alpha=0.3)

    # Plot Reward (Right Axis)
    ax2 = ax1.twinx()  # instantiate a second axes that shares the same x-axis

    color = 'tab:orange'
    ax2.set_ylabel('Average Reward', color=color, fontsize=12)
    
    # Map reward episodes to steps
    max_step = loss_timesteps[-1] if loss_timesteps else 30000
    if len(rewards) > 0:
        x_rewards = np.linspace(0, max_step, len(rewards))
        ax2.plot(x_rewards, smoothed_rewards, color=color, linewidth=2, label='Average Reward')
        ax2.tick_params(axis='y', labelcolor=color)

    # Title
    plt.title('Training Process: Loss and Average Reward', fontsize=14)
    
    # Legend
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax2.legend(lines1 + lines2, labels1 + labels2, loc='center right')

    fig.tight_layout()
    
    output_path = Path(__file__).parent / "thesis_plot.png"
    plt.savefig(output_path, dpi=300)
    print(f"Plot saved to {output_path}")

if __name__ == "__main__":
    plot_thesis_graph()
