"""Benchmark definitions and scoring for DQN autoresearch evaluation.

Provides:
- BenchmarkCase: a frozen dataclass representing a single evaluation scenario
- get_default_benchmark_cases(): deterministic list of benchmark scenarios
- compute_score(): aggregate scalar score from evaluation metrics
- generate_report(): JSON-serializable dict of evaluation results
"""

from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class BenchmarkCase:
    """A single benchmark evaluation scenario with fixed nutritional targets."""

    name: str
    target_calories: float
    target_protein: float
    target_carbs: float
    target_fat: float
    budget_limit: float


def get_default_benchmark_cases() -> List[BenchmarkCase]:
    """Return a deterministic list of benchmark cases covering diverse scenarios.

    Cases span typical use-cases: standard diet, low-budget, high-protein,
    low-calorie, and generous budget.
    """
    return [
        BenchmarkCase(
            name="standard",
            target_calories=2000.0,
            target_protein=100.0,
            target_carbs=250.0,
            target_fat=65.0,
            budget_limit=100.0,
        ),
        BenchmarkCase(
            name="low_budget",
            target_calories=1800.0,
            target_protein=80.0,
            target_carbs=230.0,
            target_fat=55.0,
            budget_limit=60.0,
        ),
        BenchmarkCase(
            name="high_protein",
            target_calories=2200.0,
            target_protein=150.0,
            target_carbs=200.0,
            target_fat=70.0,
            budget_limit=120.0,
        ),
        BenchmarkCase(
            name="low_calorie",
            target_calories=1500.0,
            target_protein=75.0,
            target_carbs=180.0,
            target_fat=50.0,
            budget_limit=80.0,
        ),
        BenchmarkCase(
            name="generous_budget",
            target_calories=2500.0,
            target_protein=120.0,
            target_carbs=300.0,
            target_fat=80.0,
            budget_limit=200.0,
        ),
        # --- 新增高难度 benchmark cases ---
        BenchmarkCase(
            name="tight_budget",
            target_calories=2000.0,
            target_protein=90.0,
            target_carbs=260.0,
            target_fat=60.0,
            budget_limit=45.0,
        ),
        BenchmarkCase(
            name="keto_diet",
            target_calories=1800.0,
            target_protein=135.0,
            target_carbs=50.0,
            target_fat=120.0,
            budget_limit=100.0,
        ),
        BenchmarkCase(
            name="bulk_diet",
            target_calories=3000.0,
            target_protein=180.0,
            target_carbs=350.0,
            target_fat=80.0,
            budget_limit=150.0,
        ),
    ]


def compute_score(
    calorie_error_pct: float,
    budget_violation_rate: float,
    diversity_score: float,
    avg_reward: float,
) -> float:
    """Compute an aggregate scalar score from evaluation metrics.

    Higher is better. The score combines calorie accuracy, budget compliance,
    menu diversity, and raw reward into a single comparable number.

    Args:
        calorie_error_pct: Mean absolute calorie error as percentage (0 = perfect).
        budget_violation_rate: Fraction of cases that exceeded budget (0-1).
        diversity_score: Mean diversity metric across cases (0-1).
        avg_reward: Mean episode reward across cases.

    Returns:
        A float score where higher is better.
    """
    # Calorie component: 100 when error is 0, drops with 3x penalty per %
    calorie_component = max(0.0, 100.0 - calorie_error_pct * 3.0)

    # Budget component: 100 when no violations, 0 when all violate
    budget_component = (1.0 - budget_violation_rate) * 100.0

    # Diversity component: 0-100 scale, floor at 3 categories minimum
    if diversity_score < 0.5:
        diversity_component = 0.0
    else:
        diversity_component = diversity_score * 100.0

    # Reward component: normalize assuming reward range ~[-10, 50]
    reward_component = max(0.0, min(100.0, (avg_reward + 10.0) * (100.0 / 60.0)))

    # Weighted combination
    score = (
        0.30 * calorie_component
        + 0.25 * budget_component
        + 0.15 * diversity_component
        + 0.30 * reward_component
    )
    return float(score)


def generate_report(
    aggregate_score: float,
    avg_reward: float,
    calorie_error_pct: float,
    budget_violation_rate: float,
    diversity_score: float,
) -> Dict[str, float]:
    """Generate a JSON-serializable evaluation report.

    Args:
        aggregate_score: Overall score from compute_score().
        avg_reward: Mean episode reward.
        calorie_error_pct: Mean calorie error percentage.
        budget_violation_rate: Fraction of budget-violating episodes.
        diversity_score: Mean diversity metric.

    Returns:
        Dict with stable keys suitable for JSON serialization.
    """
    return {
        "aggregate_score": aggregate_score,
        "avg_reward": avg_reward,
        "calorie_error_pct": calorie_error_pct,
        "budget_violation_rate": budget_violation_rate,
        "diversity_score": diversity_score,
    }
