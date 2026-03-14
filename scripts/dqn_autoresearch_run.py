"""
DQN Autoresearch 单次实验执行入口

这是 autoresearch 循环中每轮实验的执行脚本。
AI agent 不应修改此文件。

使用方式:
    uv run python scripts/dqn_autoresearch_run.py > run.log 2>&1
    uv run python scripts/dqn_autoresearch_run.py --timesteps 50000

提取结果:
    grep "^aggregate_score:\\|^avg_reward:" run.log
"""

import argparse
import io
import contextlib
import json
import sys
from datetime import datetime
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from intelligent_meal_planner.rl.autoresearch.benchmark import get_default_benchmark_cases
from intelligent_meal_planner.rl.autoresearch.evaluator import evaluate_agent


def main():
    parser = argparse.ArgumentParser(description="DQN Autoresearch Single Run")
    parser.add_argument("--timesteps", type=int, default=50000)
    parser.add_argument(
        "--output-dir",
        type=str,
        default=str(project_root / "models" / "autoresearch"),
    )
    parser.add_argument("--run-id", type=str, default=None)
    args = parser.parse_args()

    run_id = args.run_id or datetime.now().strftime("run_%Y%m%d_%H%M%S")

    # 导入可修改的训练配置（AI agent 修改 dqn_train_config.py）
    import dqn_train_config

    # 训练（输出重定向，避免环境 print 污染结果格式）
    stderr_capture = io.StringIO()
    with contextlib.redirect_stderr(stderr_capture):
        agent = dqn_train_config.train(timesteps=args.timesteps)

    # 评估（静默环境输出）
    cases = get_default_benchmark_cases()
    eval_results = evaluate_agent(agent, cases)
    report = eval_results["report"]

    # 保存 summary.json
    run_dir = Path(args.output_dir) / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    summary = {
        "run_id": run_id,
        "timesteps": args.timesteps,
        "timestamp": datetime.now().isoformat(),
        **report,
        "per_case": eval_results["per_case"],
    }

    summary_path = run_dir / "summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    # 标准化输出（供 grep 提取）
    print("---")
    print(f"aggregate_score:      {report['aggregate_score']:.6f}")
    print(f"avg_reward:           {report['avg_reward']:.6f}")
    print(f"calorie_error_pct:    {report['calorie_error_pct']:.6f}")
    print(f"budget_violation_rate: {report['budget_violation_rate']:.6f}")
    print(f"diversity_score:      {report['diversity_score']:.6f}")
    print(f"timesteps:            {args.timesteps}")
    print(f"run_id:               {run_id}")
    print(f"summary_path:         {summary_path}")


if __name__ == "__main__":
    main()
