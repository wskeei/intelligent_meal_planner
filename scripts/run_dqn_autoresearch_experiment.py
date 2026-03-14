"""Run a single DQN autoresearch experiment.

Usage:
    python scripts/run_dqn_autoresearch_experiment.py --timesteps 2000 --run-id smoke
    python scripts/run_dqn_autoresearch_experiment.py --timesteps 50000 --run-id exp001 --desc "baseline config"
"""

import argparse
import sys
from pathlib import Path

# Add project src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from intelligent_meal_planner.rl.autoresearch.runner import run_experiment


def main():
    parser = argparse.ArgumentParser(description="DQN Autoresearch Experiment Runner")
    parser.add_argument("--timesteps", type=int, default=50000, help="Training timesteps")
    parser.add_argument("--run-id", type=str, required=True, help="Unique run identifier")
    parser.add_argument("--desc", type=str, default="", help="Experiment description")
    parser.add_argument(
        "--output-dir",
        type=str,
        default=str(project_root / "models" / "autoresearch"),
        help="Base output directory",
    )
    args = parser.parse_args()

    print(f"{'=' * 60}")
    print(f"DQN Autoresearch Experiment: {args.run_id}")
    print(f"Timesteps: {args.timesteps:,}")
    print(f"Output: {args.output_dir}/{args.run_id}/")
    print(f"{'=' * 60}")

    result = run_experiment(
        run_id=args.run_id,
        timesteps=args.timesteps,
        output_dir=args.output_dir,
        description=args.desc,
    )

    report = result["report"]
    print(f"\n{'=' * 60}")
    print(f"EXPERIMENT SUMMARY")
    print(f"{'=' * 60}")
    print(f"  Aggregate Score:      {report['aggregate_score']:.2f}")
    print(f"  Avg Reward:           {report['avg_reward']:.2f}")
    print(f"  Calorie Error:        {report['calorie_error_pct']:.1f}%")
    print(f"  Budget Violation Rate: {report['budget_violation_rate']:.2f}")
    print(f"  Diversity Score:      {report['diversity_score']:.2f}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
