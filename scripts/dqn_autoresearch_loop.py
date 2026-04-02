"""DQN autoresearch loop: repeated experiments with TSV logging.

Usage:
    python scripts/dqn_autoresearch_loop.py --iterations 5 --timesteps 50000
    python scripts/dqn_autoresearch_loop.py --iterations 10 --timesteps 100000 --baseline-score 60.0
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from intelligent_meal_planner.rl.autoresearch.runner import run_experiment
from intelligent_meal_planner.rl.autoresearch.loop import (
    ensure_results_tsv,
    append_result_row,
    decide_keep_discard,
)


def main():
    parser = argparse.ArgumentParser(description="DQN Autoresearch Loop")
    parser.add_argument("--iterations", type=int, default=5, help="Number of experiments")
    parser.add_argument("--timesteps", type=int, default=50000, help="Timesteps per experiment")
    parser.add_argument("--baseline-score", type=float, default=50.0, help="Score threshold for keep/discard")
    parser.add_argument(
        "--output-dir",
        type=str,
        default=str(project_root / "models" / "autoresearch"),
        help="Base output directory",
    )
    parser.add_argument(
        "--results-tsv",
        type=str,
        default=str(project_root / "models" / "autoresearch" / "results.tsv"),
        help="Path to results TSV file",
    )
    args = parser.parse_args()

    ensure_results_tsv(args.results_tsv)
    baseline_score = args.baseline_score

    print(f"{'=' * 60}")
    print(f"DQN Autoresearch Loop")
    print(f"Iterations: {args.iterations}")
    print(f"Timesteps per run: {args.timesteps:,}")
    print(f"Baseline score: {baseline_score:.2f}")
    print(f"{'=' * 60}\n")

    for i in range(args.iterations):
        run_id = f"loop_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{i:03d}"
        description = f"loop iteration {i}"

        print(f"\n--- Iteration {i + 1}/{args.iterations}: {run_id} ---")

        result = run_experiment(
            run_id=run_id,
            timesteps=args.timesteps,
            output_dir=args.output_dir,
            description=description,
        )

        report = result["report"]
        score = report["aggregate_score"]
        decision = decide_keep_discard(score, baseline_score)

        append_result_row(
            args.results_tsv,
            run_id=run_id,
            description=description,
            aggregate_score=score,
            closed_score=report.get("closed_score", score),
            open_score=report.get("open_score", score),
            avg_reward=report["avg_reward"],
            calorie_error_pct=report["calorie_error_pct"],
            budget_violation_rate=report["budget_violation_rate"],
            diversity_score=report["diversity_score"],
            decision=decision,
        )

        print(f"  Score: {score:.2f} -> {decision.upper()}")

        # Update baseline if kept
        if decision == "keep" and score > baseline_score:
            baseline_score = score
            print(f"  New baseline: {baseline_score:.2f}")

    print(f"\n{'=' * 60}")
    print(f"Loop complete. Results at: {args.results_tsv}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
