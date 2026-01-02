"""
论文绘图脚本
用于从 Monitor 日志文件中生成高质量的训练曲线图
"""

import os
import argparse
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

def plot_training_results(log_dir: str, output_dir: str = None, smooth_window: int = 100):
    """
    绘制训练结果
    """
    log_dir = Path(log_dir)
    if output_dir is None:
        output_dir = log_dir / "plots"
    else:
        output_dir = Path(output_dir)
        
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 查找 monitor.csv 文件
    # 通常 Monitor wrapper 会生成 {name}.monitor.csv
    monitor_files = list(log_dir.glob("*.monitor.csv"))
    if not monitor_files:
        # 尝试查找直接的 monitor.csv (如果名字没后缀)
        monitor_files = list(log_dir.glob("monitor.csv"))
        
    if not monitor_files:
        print(f"在 {log_dir} 中未找到 monitor.csv 文件")
        return

    print(f"找到日志文件: {[f.name for f in monitor_files]}")
    
    # 设置绘图风格
    sns.set_theme(style="whitegrid", context="paper", font_scale=1.2)
    # 尝试设置中文字体，如果需要的话 (SimHei usually works on Windows)
    try:
        plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial', 'Microsoft YaHei'] 
        plt.rcParams['axes.unicode_minus'] = False
    except:
        pass
    
    for log_file in monitor_files:
        try:
            # 读取日志，跳过前两行 (metadata)
            df = pd.read_csv(log_file, skiprows=1)
            
            if 'r' not in df.columns or 'l' not in df.columns:
                print(f"文件 {log_file} 列名不匹配，跳过")
                continue
                
            # 计算累积步数
            if 't' in df.columns:
                df['timesteps'] = df['t']
            else:
                df['timesteps'] = df['l'].cumsum()
                
            # 平滑处理
            df['reward_smooth'] = df['r'].rolling(window=smooth_window, min_periods=1).mean()
            df['length_smooth'] = df['l'].rolling(window=smooth_window, min_periods=1).mean()
            
            # 1. 绘制奖励曲线
            plt.figure(figsize=(10, 6))
            sns.lineplot(data=df, x='timesteps', y='reward_smooth', linewidth=2, color='#2878B5')
            plt.fill_between(df['timesteps'], 
                             df['r'].rolling(window=smooth_window, min_periods=1).min(),
                             df['r'].rolling(window=smooth_window, min_periods=1).max(),
                             alpha=0.2, color='#2878B5')
            
            plt.title(f"训练奖励曲线 (平滑窗口={smooth_window})", fontsize=14)
            plt.xlabel("训练步数", fontsize=12)
            plt.ylabel("平均回合奖励", fontsize=12)
            plt.tight_layout()
            save_path = output_dir / f"{log_file.stem}_rewards.png"
            plt.savefig(save_path, dpi=300)
            print(f"保存奖励图表: {save_path}")
            plt.close()
            
            # 2. 绘制回合长度曲线
            plt.figure(figsize=(10, 6))
            sns.lineplot(data=df, x='timesteps', y='length_smooth', linewidth=2, color='#C82423')
            plt.title(f"训练回合长度曲线 (平滑窗口={smooth_window})", fontsize=14)
            plt.xlabel("训练步数", fontsize=12)
            plt.ylabel("平均回合步数", fontsize=12)
            # 添加目标线 (通常是 max_steps)
            # 假设 9 (3餐 * 3项)
            plt.axhline(y=9, color='green', linestyle='--', label='目标步数 (9)')
            plt.legend()
            
            plt.tight_layout()
            save_path = output_dir / f"{log_file.stem}_lengths.png"
            plt.savefig(save_path, dpi=300)
            print(f"保存长度图表: {save_path}")
            plt.close()
            
        except Exception as e:
            print(f"处理文件 {log_file} 时出错: {e}")

def main():
    parser = argparse.ArgumentParser(description="绘制 RL 训练曲线")
    parser.add_argument("--log-dir", type=str, required=True, help="包含 monitor.csv 的日志目录")
    parser.add_argument("--output-dir", type=str, default=None, help="图片输出目录")
    parser.add_argument("--smooth", type=int, default=100, help="平滑窗口大小")
    
    args = parser.parse_args()
    
    plot_training_results(args.log_dir, args.output_dir, args.smooth)

if __name__ == "__main__":
    main()
