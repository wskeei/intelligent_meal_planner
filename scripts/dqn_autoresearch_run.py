"""
DQN Autoresearch 单次实验执行入口

这是 autoresearch 循环中每轮实验的执行脚本。
AI agent 不应修改此文件。

使用方式 (conda ai_lab + GPU):
    conda activate ai_lab
    python scripts/dqn_autoresearch_run.py > run.log 2>&1
    python scripts/dqn_autoresearch_run.py --timesteps 50000

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
sys.path.insert(0, str(project_root / "scripts"))

from intelligent_meal_planner.rl.autoresearch.benchmark import get_default_benchmark_cases
from intelligent_meal_planner.rl.autoresearch.evaluator import evaluate_agent_dual
from intelligent_meal_planner.rl.autoresearch.recipe_validator import validate_recipes


def main():
    parser = argparse.ArgumentParser(description="DQN Autoresearch Single Run")
    parser.add_argument("--timesteps", type=int, default=50000)
    parser.add_argument(
        "--output-dir", type=str,
        default=str(project_root / "models" / "autoresearch"),
    )
    parser.add_argument("--run-id", type=str, default=None)
    args = parser.parse_args()

    run_id = args.run_id or datetime.now().strftime("run_%Y%m%d_%H%M%S")

    import dqn_train_config

    config = dqn_train_config.get_config(args.timesteps)
    price_scale = config.get("price_scale", 1.0)
    budget_scale = config.get("budget_scale", 1.0)
    raw_custom_recipes = config.get("custom_recipes", [])

    valid_recipes, validation_errors = validate_recipes(raw_custom_recipes)
    n_custom_recipes = len(valid_recipes)

    if validation_errors:
        print(f"[WARN] {len(validation_errors)} custom recipe(s) rejected:")
        for err in validation_errors:
            print(f"  - {err}")
    if valid_recipes:
        print(f"[INFO] {n_custom_recipes} custom recipe(s) accepted")

    stderr_capture = io.StringIO()
    with contextlib.redirect_stderr(stderr_capture):
        agent = dqn_train_config.train(timesteps=args.timesteps)

    cases = get_default_benchmark_cases()
    eval_results = evaluate_agent_dual(
        agent, cases,
        price_scale=price_scale, budget_scale=budget_scale,
        custom_recipes=valid_recipes if valid_recipes else None,
    )
    report = eval_results["report"]

    run_dir = Path(args.output_dir) / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    summary = {
        "run_id": run_id,
        "timesteps": args.timesteps,
        "timestamp": datetime.now().isoformat(),
        "price_scale": price_scale,
        "budget_scale": budget_scale,
        "n_custom_recipes": n_custom_recipes,
        **report,
        "closed_per_case": eval_results["closed_result"]["per_case"],
        "open_per_case": eval_results["open_result"]["per_case"],
    }

    summary_path = run_dir / "summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print("---")
    print(f"aggregate_score:      {report['aggregate_score']:.6f}")
    print(f"closed_score:         {report['closed_score']:.6f}")
    print(f"open_score:           {report['open_score']:.6f}")
    print(f"avg_reward:           {report['avg_reward']:.6f}")
    print(f"calorie_error_pct:    {report['calorie_error_pct']:.6f}")
    print(f"budget_violation_rate: {report['budget_violation_rate']:.6f}")
    print(f"diversity_score:      {report['diversity_score']:.6f}")
    print(f"price_scale:          {price_scale:.2f}")
    print(f"budget_scale:         {budget_scale:.2f}")
    print(f"n_custom_recipes:     {n_custom_recipes}")
    print(f"timesteps:            {args.timesteps}")
    print(f"run_id:               {run_id}")
    print(f"summary_path:         {summary_path}")


if __name__ == "__main__":
    main()
