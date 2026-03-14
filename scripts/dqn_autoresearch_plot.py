"""DQN Autoresearch 进度可视化

从 results.tsv 读取实验结果，生成进度图。
每轮实验后自动调用，也可独立运行查看当前进度。

独立运行:
    conda activate ai_lab
    python scripts/dqn_autoresearch_plot.py
    python scripts/dqn_autoresearch_plot.py --tsv models/autoresearch/results.tsv
"""

import argparse
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # 无头模式，不弹窗
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np

project_root = Path(__file__).parent.parent

# results.tsv 表头列定义
COLUMNS = [
    "run_id", "description", "aggregate_score", "avg_reward",
    "calorie_error_pct", "budget_violation_rate", "diversity_score", "decision",
]


def parse_results_tsv(tsv_path: str) -> dict:
    """解析 results.tsv，返回按列组织的数据字典。"""
    data = {col: [] for col in COLUMNS}
    data["index"] = []

    p = Path(tsv_path)
    if not p.exists():
        return data

    lines = p.read_text(encoding="utf-8").strip().split("\n")
    if len(lines) <= 1:
        return data  # 只有表头

    for i, line in enumerate(lines[1:]):  # 跳过表头
        fields = line.split("\t")
        if len(fields) < len(COLUMNS):
            continue
        data["index"].append(i + 1)
        data["run_id"].append(fields[0])
        data["description"].append(fields[1])
        data["aggregate_score"].append(float(fields[2]))
        data["avg_reward"].append(float(fields[3]))
        data["calorie_error_pct"].append(float(fields[4]))
        data["budget_violation_rate"].append(float(fields[5]))
        data["diversity_score"].append(float(fields[6]))
        data["decision"].append(fields[7])

    return data


def plot_progress(tsv_path: str, output_path: str = None) -> str:
    """生成进度图并保存为 PNG。

    Args:
        tsv_path: results.tsv 路径。
        output_path: 输出 PNG 路径。默认保存在 tsv 同目录下。

    Returns:
        保存的图片路径。
    """
    data = parse_results_tsv(tsv_path)

    if not data["index"]:
        print("No experiment results to plot.")
        return ""

    if output_path is None:
        output_path = str(Path(tsv_path).parent / "progress.png")

    n = len(data["index"])
    x = np.array(data["index"])
    scores = np.array(data["aggregate_score"])
    rewards = np.array(data["avg_reward"])
    cal_err = np.array(data["calorie_error_pct"])
    budget_viol = np.array(data["budget_violation_rate"])
    diversity = np.array(data["diversity_score"])
    decisions = data["decision"]

    # 计算 best-so-far 线
    best_so_far = np.maximum.accumulate(scores)

    # keep/discard 颜色
    colors = ["#2ecc71" if d == "keep" else "#e74c3c" if d == "discard" else "#95a5a6"
              for d in decisions]

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle(
        f"DQN Autoresearch Progress  ({n} experiments)",
        fontsize=16, fontweight="bold", y=0.98,
    )

    # --- 子图 1: Aggregate Score (主图) ---
    ax = axes[0, 0]
    ax.scatter(x, scores, c=colors, s=50, zorder=3, edgecolors="white", linewidths=0.5)
    ax.plot(x, best_so_far, color="#3498db", linewidth=2, label="Best so far", zorder=2)
    ax.fill_between(x, best_so_far, alpha=0.1, color="#3498db")
    ax.set_xlabel("Experiment #")
    ax.set_ylabel("Aggregate Score")
    ax.set_title("Aggregate Score (higher = better)")
    ax.legend(loc="lower right")
    ax.grid(True, alpha=0.3)
    ax.xaxis.set_major_locator(ticker.MaxNLocator(integer=True))
    # 标注最佳分数
    best_idx = np.argmax(scores)
    ax.annotate(
        f"Best: {scores[best_idx]:.1f}",
        xy=(x[best_idx], scores[best_idx]),
        xytext=(10, 10), textcoords="offset points",
        fontsize=9, fontweight="bold", color="#2c3e50",
        arrowprops=dict(arrowstyle="->", color="#2c3e50"),
    )

    # --- 子图 2: Avg Reward ---
    ax = axes[0, 1]
    ax.scatter(x, rewards, c=colors, s=50, zorder=3, edgecolors="white", linewidths=0.5)
    best_reward_so_far = np.maximum.accumulate(rewards)
    ax.plot(x, best_reward_so_far, color="#9b59b6", linewidth=2, label="Best so far")
    ax.set_xlabel("Experiment #")
    ax.set_ylabel("Avg Reward")
    ax.set_title("Average Episode Reward")
    ax.legend(loc="lower right")
    ax.grid(True, alpha=0.3)
    ax.xaxis.set_major_locator(ticker.MaxNLocator(integer=True))

    # --- 子图 3: Calorie Error + Budget Violation ---
    ax = axes[1, 0]
    ax.scatter(x, cal_err, c=colors, s=40, marker="o", label="Calorie Error %", zorder=3)
    ax2 = ax.twinx()
    ax2.scatter(x, budget_viol * 100, c=colors, s=40, marker="s", alpha=0.6, zorder=3)
    ax2.set_ylabel("Budget Violation %", color="#e67e22")
    ax2.tick_params(axis="y", labelcolor="#e67e22")
    ax.set_xlabel("Experiment #")
    ax.set_ylabel("Calorie Error %")
    ax.set_title("Calorie Error & Budget Violations (lower = better)")
    ax.grid(True, alpha=0.3)
    ax.xaxis.set_major_locator(ticker.MaxNLocator(integer=True))
    # 手工图例
    from matplotlib.lines import Line2D
    legend_elements = [
        Line2D([0], [0], marker="o", color="w", markerfacecolor="#666", label="Cal Error %", markersize=8),
        Line2D([0], [0], marker="s", color="w", markerfacecolor="#e67e22", label="Budget Viol %", markersize=8),
    ]
    ax.legend(handles=legend_elements, loc="upper right", fontsize=8)

    # --- 子图 4: Keep/Discard 统计 + Diversity ---
    ax = axes[1, 1]
    keep_count = sum(1 for d in decisions if d == "keep")
    discard_count = sum(1 for d in decisions if d == "discard")
    crash_count = sum(1 for d in decisions if d == "crash")

    # 左半边: 饼图
    ax_pie = fig.add_axes([0.58, 0.08, 0.15, 0.15])  # 小饼图嵌入
    sizes = [keep_count, discard_count, crash_count]
    labels_pie = [f"Keep ({keep_count})", f"Discard ({discard_count})", f"Crash ({crash_count})"]
    pie_colors = ["#2ecc71", "#e74c3c", "#95a5a6"]
    # 过滤掉 0 值
    nonzero = [(s, l, c) for s, l, c in zip(sizes, labels_pie, pie_colors) if s > 0]
    if nonzero:
        ax_pie.pie(
            [s for s, _, _ in nonzero],
            labels=[l for _, l, _ in nonzero],
            colors=[c for _, _, c in nonzero],
            autopct="%1.0f%%", startangle=90, textprops={"fontsize": 7},
        )
    ax_pie.set_title("Decisions", fontsize=8, fontweight="bold")

    # 右半边: Diversity
    ax.scatter(x, diversity, c=colors, s=50, zorder=3, edgecolors="white", linewidths=0.5)
    ax.set_xlabel("Experiment #")
    ax.set_ylabel("Diversity Score")
    ax.set_title("Menu Diversity (higher = better)")
    ax.set_ylim(-0.05, 1.05)
    ax.grid(True, alpha=0.3)
    ax.xaxis.set_major_locator(ticker.MaxNLocator(integer=True))

    # 图例说明
    from matplotlib.patches import Patch
    legend_patches = [
        Patch(facecolor="#2ecc71", label="Keep"),
        Patch(facecolor="#e74c3c", label="Discard"),
        Patch(facecolor="#95a5a6", label="Crash"),
    ]
    fig.legend(
        handles=legend_patches, loc="lower center", ncol=3,
        fontsize=10, frameon=True, bbox_to_anchor=(0.5, 0.0),
    )

    plt.subplots_adjust(left=0.08, right=0.95, top=0.92, bottom=0.08, hspace=0.35, wspace=0.3)
    fig.savefig(output_path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)

    print(f"Progress plot saved: {output_path}")
    return output_path


def main():
    parser = argparse.ArgumentParser(description="DQN Autoresearch Progress Plot")
    parser.add_argument(
        "--tsv", type=str,
        default=str(project_root / "models" / "autoresearch" / "results.tsv"),
        help="Path to results.tsv",
    )
    parser.add_argument(
        "--output", type=str, default=None,
        help="Output PNG path (default: same dir as tsv)",
    )
    args = parser.parse_args()

    plot_progress(args.tsv, args.output)


if __name__ == "__main__":
    main()
