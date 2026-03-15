"""DQN Autoresearch 进度可视化

从 results.tsv 读取实验结果，生成进度图。
每轮实验后自动调用，也可独立运行查看当前进度。

独立运行:
    conda activate ai_lab
    python scripts/dqn_autoresearch_plot.py
    python scripts/dqn_autoresearch_plot.py --tsv models/autoresearch/results.tsv
"""

import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np


project_root = Path(__file__).parent.parent


def parse_results_tsv(tsv_path: str) -> dict:
    """解析 results.tsv，返回按列组织的数据字典。自动兼容各版本格式。"""
    data = {
        "index": [], "run_id": [], "description": [],
        "aggregate_score": [], "closed_score": [], "open_score": [],
        "avg_reward": [], "calorie_error_pct": [], "budget_violation_rate": [],
        "diversity_score": [], "price_scale": [], "budget_scale": [],
        "n_custom_recipes": [], "decision": [],
    }

    p = Path(tsv_path)
    if not p.exists():
        return data

    lines = p.read_text(encoding="utf-8").strip().split("\n")
    if len(lines) <= 1:
        return data

    header = lines[0].split("\t")
    col_index = {name: i for i, name in enumerate(header)}

    for i, line in enumerate(lines[1:]):
        fields = line.split("\t")
        if len(fields) < 3:
            continue
        data["index"].append(i + 1)
        data["run_id"].append(fields[col_index.get("run_id", 0)])
        data["description"].append(fields[col_index.get("description", 1)])
        data["aggregate_score"].append(float(fields[col_index["aggregate_score"]]) if "aggregate_score" in col_index else 0.0)
        data["closed_score"].append(float(fields[col_index["closed_score"]]) if "closed_score" in col_index else 0.0)
        data["open_score"].append(float(fields[col_index["open_score"]]) if "open_score" in col_index else 0.0)
        data["avg_reward"].append(float(fields[col_index["avg_reward"]]) if "avg_reward" in col_index else 0.0)
        data["calorie_error_pct"].append(float(fields[col_index["calorie_error_pct"]]) if "calorie_error_pct" in col_index else 0.0)
        data["budget_violation_rate"].append(float(fields[col_index["budget_violation_rate"]]) if "budget_violation_rate" in col_index else 0.0)
        data["diversity_score"].append(float(fields[col_index["diversity_score"]]) if "diversity_score" in col_index else 0.0)
        data["price_scale"].append(float(fields[col_index["price_scale"]]) if "price_scale" in col_index else 1.0)
        data["budget_scale"].append(float(fields[col_index["budget_scale"]]) if "budget_scale" in col_index else 1.0)
        data["n_custom_recipes"].append(int(fields[col_index["n_custom_recipes"]]) if "n_custom_recipes" in col_index else 0)
        data["decision"].append(fields[col_index["decision"]] if "decision" in col_index else "unknown")

    return data


def plot_progress(tsv_path: str, output_path: str = None) -> str:
    """生成进度图并保存为 PNG。"""
    data = parse_results_tsv(tsv_path)
    if not data["index"]:
        print("No experiment results to plot.")
        return ""
    if output_path is None:
        output_path = str(Path(tsv_path).parent / "progress.png")

    n = len(data["index"])
    x = np.array(data["index"])
    scores = np.array(data["aggregate_score"])
    closed = np.array(data["closed_score"])
    opened = np.array(data["open_score"])
    rewards = np.array(data["avg_reward"])
    cal_err = np.array(data["calorie_error_pct"])
    budget_viol = np.array(data["budget_violation_rate"])
    diversity = np.array(data["diversity_score"])
    n_custom = np.array(data["n_custom_recipes"])
    decisions = data["decision"]

    has_dual = np.any(closed != 0) or np.any(opened != 0)
    colors = ["#2ecc71" if d == "keep" else "#e74c3c" if d == "discard" else "#95a5a6"
              for d in decisions]

    fig, axes = plt.subplots(2, 3, figsize=(20, 10))
    fig.suptitle(f"DQN Autoresearch Progress  ({n} experiments)",
                 fontsize=16, fontweight="bold", y=0.98)

    # 1: Aggregate Score
    ax = axes[0, 0]
    best_so_far = np.maximum.accumulate(scores)
    ax.scatter(x, scores, c=colors, s=50, zorder=3, edgecolors="white", linewidths=0.5)
    ax.plot(x, best_so_far, color="#3498db", linewidth=2, label="Best so far", zorder=2)
    ax.fill_between(x, best_so_far, alpha=0.1, color="#3498db")
    if has_dual:
        ax.plot(x, closed, color="#e67e22", linewidth=1.5, alpha=0.7, linestyle="--", label="Closed")
        ax.plot(x, opened, color="#27ae60", linewidth=1.5, alpha=0.7, linestyle=":", label="Open")
    ax.set_xlabel("Experiment #"); ax.set_ylabel("Score")
    ax.set_title("Aggregate Score = 0.5*Closed + 0.5*Open" if has_dual else "Aggregate Score")
    ax.legend(loc="lower right", fontsize=8); ax.grid(True, alpha=0.3)
    ax.xaxis.set_major_locator(ticker.MaxNLocator(integer=True))
    best_idx = np.argmax(scores)
    ax.annotate(f"Best: {scores[best_idx]:.1f}", xy=(x[best_idx], scores[best_idx]),
                xytext=(10, 10), textcoords="offset points", fontsize=9, fontweight="bold",
                color="#2c3e50", arrowprops=dict(arrowstyle="->", color="#2c3e50"))

    # 2: Avg Reward
    ax = axes[0, 1]
    ax.scatter(x, rewards, c=colors, s=50, zorder=3, edgecolors="white", linewidths=0.5)
    ax.plot(x, np.maximum.accumulate(rewards), color="#9b59b6", linewidth=2, label="Best so far")
    ax.set_xlabel("Experiment #"); ax.set_ylabel("Avg Reward")
    ax.set_title("Average Episode Reward"); ax.legend(loc="lower right")
    ax.grid(True, alpha=0.3); ax.xaxis.set_major_locator(ticker.MaxNLocator(integer=True))

    # 3: Custom Recipes
    ax = axes[0, 2]
    ax.bar(x, n_custom, color=[c + "99" for c in colors], edgecolor=colors, linewidth=1)
    ax.set_xlabel("Experiment #"); ax.set_ylabel("# Custom Recipes")
    ax.set_title("Custom Recipes Added"); ax.grid(True, alpha=0.3, axis="y")
    ax.xaxis.set_major_locator(ticker.MaxNLocator(integer=True))

    # 4: Calorie Error + Budget Violation
    ax = axes[1, 0]
    ax.scatter(x, cal_err, c=colors, s=40, marker="o", zorder=3)
    ax2 = ax.twinx()
    ax2.scatter(x, budget_viol * 100, c=colors, s=40, marker="s", alpha=0.6, zorder=3)
    ax2.set_ylabel("Budget Violation %", color="#e67e22")
    ax2.tick_params(axis="y", labelcolor="#e67e22")
    ax.set_xlabel("Experiment #"); ax.set_ylabel("Calorie Error %")
    ax.set_title("Calorie Error & Budget Violations (lower = better)")
    ax.grid(True, alpha=0.3); ax.xaxis.set_major_locator(ticker.MaxNLocator(integer=True))
    from matplotlib.lines import Line2D
    ax.legend(handles=[
        Line2D([0], [0], marker="o", color="w", markerfacecolor="#666", label="Cal Error %", markersize=8),
        Line2D([0], [0], marker="s", color="w", markerfacecolor="#e67e22", label="Budget Viol %", markersize=8),
    ], loc="upper right", fontsize=8)

    # 5: Diversity
    ax = axes[1, 1]
    ax.scatter(x, diversity, c=colors, s=50, zorder=3, edgecolors="white", linewidths=0.5)
    ax.axhline(y=0.5, color="#e74c3c", linestyle="--", linewidth=1, alpha=0.5, label="Min threshold (3 cats)")
    ax.set_xlabel("Experiment #"); ax.set_ylabel("Diversity Score")
    ax.set_title("Menu Diversity (higher = better)"); ax.set_ylim(-0.05, 1.05)
    ax.legend(loc="lower right", fontsize=8); ax.grid(True, alpha=0.3)
    ax.xaxis.set_major_locator(ticker.MaxNLocator(integer=True))

    # 6: Pie chart
    ax = axes[1, 2]
    keep_count = sum(1 for d in decisions if d == "keep")
    discard_count = sum(1 for d in decisions if d == "discard")
    crash_count = sum(1 for d in decisions if d == "crash")
    sizes = [keep_count, discard_count, crash_count]
    labels_pie = [f"Keep ({keep_count})", f"Discard ({discard_count})", f"Crash ({crash_count})"]
    pie_colors = ["#2ecc71", "#e74c3c", "#95a5a6"]
    nonzero = [(s, l, c) for s, l, c in zip(sizes, labels_pie, pie_colors) if s > 0]
    if nonzero:
        ax.pie([s for s, _, _ in nonzero], labels=[l for _, l, _ in nonzero],
               colors=[c for _, _, c in nonzero], autopct="%1.0f%%", startangle=90,
               textprops={"fontsize": 9})
    ax.set_title("Keep / Discard / Crash")

    from matplotlib.patches import Patch
    fig.legend(handles=[Patch(facecolor="#2ecc71", label="Keep"),
                        Patch(facecolor="#e74c3c", label="Discard"),
                        Patch(facecolor="#95a5a6", label="Crash")],
               loc="lower center", ncol=3, fontsize=10, frameon=True, bbox_to_anchor=(0.5, 0.0))

    plt.subplots_adjust(left=0.06, right=0.96, top=0.92, bottom=0.08, hspace=0.35, wspace=0.35)
    fig.savefig(output_path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"Progress plot saved: {output_path}")
    return output_path


def main():
    parser = argparse.ArgumentParser(description="DQN Autoresearch Progress Plot")
    parser.add_argument("--tsv", type=str,
                        default=str(project_root / "models" / "autoresearch" / "results.tsv"))
    parser.add_argument("--output", type=str, default=None)
    args = parser.parse_args()
    plot_progress(args.tsv, args.output)


if __name__ == "__main__":
    main()
