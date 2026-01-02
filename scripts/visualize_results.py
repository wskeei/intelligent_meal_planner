import pandas as pd
import matplotlib.pyplot as plt
import os

# Define the log file path
log_file = r"D:\Project\intelligent_meal_planner\models\logs\monitor.csv"
output_file = r"D:\Project\intelligent_meal_planner\training_results.png"

def plot_results():
    if not os.path.exists(log_file):
        print(f"Error: Log file not found at {log_file}")
        return

    try:
        # Read the CSV file, skipping the first metadata line
        df = pd.read_csv(log_file, skiprows=1)
        
        # Check if necessary columns exist
        if 'r' not in df.columns or 'l' not in df.columns:
            print("Error: Expected columns 'r' (reward) and 'l' (length) not found.")
            print(f"Found columns: {df.columns}")
            return

        # Calculate rolling averages to smooth the plots
        window_size = 100
        df['reward_rolling'] = df['r'].rolling(window=window_size).mean()
        df['length_rolling'] = df['l'].rolling(window=window_size).mean()

        # Create the plot
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 10), sharex=True)

        # Plot Rewards
        ax1.plot(df.index, df['r'], alpha=0.3, color='gray', label='Raw Reward')
        ax1.plot(df.index, df['reward_rolling'], color='blue', label=f'Rolling Mean ({window_size})')
        ax1.set_ylabel('Episode Reward')
        ax1.set_title('Training Rewards over Episodes')
        ax1.legend()
        ax1.grid(True, alpha=0.3)

        # Plot Episode Lengths
        ax2.plot(df.index, df['l'], alpha=0.3, color='gray', label='Raw Length')
        ax2.plot(df.index, df['length_rolling'], color='green', label=f'Rolling Mean ({window_size})')
        ax2.set_ylabel('Episode Length')
        ax2.set_xlabel('Episode')
        ax2.set_title('Episode Length over Episodes')
        ax2.legend()
        ax2.grid(True, alpha=0.3)

        # Adjust layout and save
        plt.tight_layout()
        plt.savefig(output_file)
        print(f"Successfully saved training visualization to: {output_file}")
        
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    plot_results()
