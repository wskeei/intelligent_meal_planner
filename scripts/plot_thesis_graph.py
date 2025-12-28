
import json
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

# Set font to support Chinese characters if available, otherwise fallback
# For standard matplotlib, usually need to configure font properties
from matplotlib.font_manager import FontProperties

def moving_average(data, window_size=50):
    return np.convolve(data, np.ones(window_size)/window_size, mode='valid')

def plot_thesis_graph():
    data_path = Path(__file__).parent / "thesis_training_data.json"
    if not data_path.exists():
        print(f"Data file not found: {data_path}")
        return

    with open(data_path, 'r') as f:
        data = json.load(f)

    losses = data.get("loss_history", [])
    # Loss is logged per training step (or however we captured it). 
    # It might be very noisy. Let's smooth it.
    
    rewards = data.get("episode_rewards", [])
    
    # Smooth data
    # Adjust window size based on data length
    loss_window = max(1, len(losses) // 100)
    reward_window = max(1, len(rewards) // 20)
    
    smoothed_losses = moving_average(losses, window_size=loss_window)
    smoothed_rewards = moving_average(rewards, window_size=reward_window)
    
    # Create plot
    fig, ax1 = plt.subplots(figsize=(10, 6))

    # Plot Loss (Left Axis)
    color = 'tab:blue'
    ax1.set_xlabel('Training Steps (x100)', fontsize=12) # Approximation if we don't have exact x-axis alignment
    # Actually we have "loss_timesteps", let's use them if possible, but indices are fine for "General Trend"
    
    # If we have loss_timesteps, use them
    loss_timesteps = data.get("loss_timesteps", [])
    if len(loss_timesteps) == len(losses):
        # Align moving average x-axis
        x_loss = loss_timesteps[loss_window-1:]
    else:
        x_loss = range(len(smoothed_losses))
        
    ax1.set_ylabel('Loss (MSE)', color=color, fontsize=12)
    ax1.plot(x_loss, smoothed_losses, color=color, linewidth=2, label='Loss')
    ax1.tick_params(axis='y', labelcolor=color)
    ax1.grid(True, alpha=0.3)

    # Plot Reward (Right Axis)
    ax2 = ax1.twinx()  # instantiate a second axes that shares the same x-axis

    color = 'tab:orange'
    ax2.set_ylabel('Average Reward', color=color, fontsize=12)  # we already handled the x-label with ax1
    
    # We need to map reward episodes to steps roughly.
    # Total steps = 20k.
    # We have N episodes.
    # Let's just map it linearly to the max timestep for visual correlation
    max_step = loss_timesteps[-1] if loss_timesteps else 20000
    x_rewards = np.linspace(0, max_step, len(smoothed_rewards))
    
    ax2.plot(x_rewards, smoothed_rewards, color=color, linewidth=2, label='Average Reward')
    ax2.tick_params(axis='y', labelcolor=color)

    # Title
    plt.title('Training Process: Loss and Average Reward', fontsize=14)
    
    # Legend
    # Combine legends
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax2.legend(lines1 + lines2, labels1 + labels2, loc='center right')

    fig.tight_layout()  # otherwise the right y-label is slightly clipped
    
    output_path = Path(__file__).parent / "thesis_plot.png"
    plt.savefig(output_path, dpi=300)
    print(f"Plot saved to {output_path}")

if __name__ == "__main__":
    plot_thesis_graph()
