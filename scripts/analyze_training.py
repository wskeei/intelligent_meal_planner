"""分析训练结果"""
import sys
sys.path.insert(0, 'src')

import numpy as np
import os

# 读取评估数据
eval_path = "models/logs/eval/evaluations.npz"
if os.path.exists(eval_path):
    data = np.load(eval_path)

    timesteps = data['timesteps']
    results = data['results']  # shape: (n_evals, n_episodes)
    ep_lengths = data['ep_lengths']

    print("=" * 70)
    print("TRAINING EVALUATION RESULTS")
    print("=" * 70)

    print(f"\nTotal evaluations: {len(timesteps)}")
    print(f"Episodes per eval: {results.shape[1]}")

    # 计算每次评估的平均奖励
    mean_rewards = np.mean(results, axis=1)
    std_rewards = np.std(results, axis=1)

    print(f"\n{'Step':>10} | {'Mean Reward':>12} | {'Std':>8} | {'Min':>8} | {'Max':>8}")
    print("-" * 60)

    # 显示关键节点
    key_indices = [0, len(timesteps)//4, len(timesteps)//2, 3*len(timesteps)//4, -1]
    for idx in key_indices:
        if idx < 0:
            idx = len(timesteps) + idx
        if idx < len(timesteps):
            print(f"{timesteps[idx]:>10,} | {mean_rewards[idx]:>12.2f} | {std_rewards[idx]:>8.2f} | "
                  f"{np.min(results[idx]):>8.2f} | {np.max(results[idx]):>8.2f}")

    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    # 初始 vs 最终
    initial_reward = mean_rewards[0]
    final_reward = mean_rewards[-1]
    best_reward = np.max(mean_rewards)
    best_step = timesteps[np.argmax(mean_rewards)]

    print(f"\nInitial Reward (step {timesteps[0]:,}):  {initial_reward:.2f}")
    print(f"Final Reward (step {timesteps[-1]:,}):    {final_reward:.2f}")
    print(f"Best Reward (step {best_step:,}):         {best_reward:.2f}")
    print(f"Improvement:                        {final_reward - initial_reward:+.2f}")

    # 判断是否达标
    print("\n" + "=" * 70)
    print("GOAL ASSESSMENT")
    print("=" * 70)

    target_reward = 8.0  # 我们设定的目标

    if final_reward >= target_reward:
        print(f"\n✅ SUCCESS! Final reward ({final_reward:.2f}) >= Target ({target_reward})")
    elif final_reward >= 0:
        print(f"\n⚠️  PARTIAL SUCCESS: Reward is positive ({final_reward:.2f}), but below target ({target_reward})")
        print(f"   Recommendation: Continue training for another 200k-500k steps")
    elif final_reward > initial_reward:
        print(f"\n⚠️  LEARNING: Model is improving ({initial_reward:.2f} -> {final_reward:.2f})")
        print(f"   Recommendation: Continue training, model hasn't converged yet")
    else:
        print(f"\n❌ NOT LEARNING: Reward not improving significantly")
        print(f"   Recommendation: Check reward function and environment")

    # 趋势分析
    print("\n" + "-" * 70)
    print("TREND ANALYSIS (last 10 evaluations)")
    print("-" * 70)

    if len(mean_rewards) >= 10:
        recent = mean_rewards[-10:]
        trend = np.polyfit(range(10), recent, 1)[0]
        print(f"Recent rewards: {recent}")
        print(f"Trend slope: {trend:.4f} per eval")
        if trend > 0.1:
            print("���� Reward is still increasing - training should continue")
        elif trend > -0.1:
            print("📊 Reward has stabilized - may have converged")
        else:
            print("📉 Reward is decreasing - possible overfitting or instability")

    print("\n" + "=" * 70)
else:
    print(f"Evaluation file not found: {eval_path}")
