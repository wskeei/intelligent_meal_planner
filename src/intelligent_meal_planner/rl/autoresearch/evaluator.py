"""Deterministic evaluator for trained DQN checkpoints.

Runs an agent through a set of benchmark cases using MealPlanningEnv in
evaluation (non-training) mode and collects per-case metrics.
"""

import io
import contextlib
import numpy as np
from typing import Any, Dict, List, Protocol, runtime_checkable

from intelligent_meal_planner.rl.environment import MealPlanningEnv
from intelligent_meal_planner.rl.autoresearch.benchmark import (
    BenchmarkCase,
    compute_score,
    generate_report,
)


@runtime_checkable
class AgentProtocol(Protocol):
    """Protocol that both MaskableDQNAgent and test doubles must satisfy."""

    def select_action(
        self,
        state: np.ndarray,
        action_mask: np.ndarray,
        step: int,
        deterministic: bool = True,
    ) -> int: ...


def _run_single_case(agent: AgentProtocol, case: BenchmarkCase) -> Dict[str, Any]:
    """Run one benchmark case and return per-case metrics."""
    env = MealPlanningEnv(
        target_calories=case.target_calories,
        target_protein=case.target_protein,
        target_carbs=case.target_carbs,
        target_fat=case.target_fat,
        budget_limit=case.budget_limit,
        training_mode=False,
    )

    # Suppress env print statements during evaluation
    with contextlib.redirect_stdout(io.StringIO()):
        obs, info = env.reset()

        total_reward = 0.0
        step = 0
        done = False

        while not done:
            mask = env.action_masks()
            action = agent.select_action(obs, mask, step=step, deterministic=True)
            obs, reward, terminated, truncated, info = env.step(action)
            total_reward += reward
            step += 1
            done = terminated or truncated

    return {
        "case_name": case.name,
        "total_reward": float(total_reward),
        "total_calories": float(env.total_calories),
        "total_cost": float(env.total_cost),
        "target_calories": case.target_calories,
        "budget_limit": case.budget_limit,
        "unique_categories": len(set(env.selected_categories)),
        "calorie_error_pct": abs(env.total_calories - case.target_calories)
        / case.target_calories
        * 100.0,
        "budget_violated": env.total_cost > case.budget_limit,
    }


def evaluate_agent(
    agent: AgentProtocol,
    cases: List[BenchmarkCase],
) -> Dict[str, Any]:
    """Evaluate an agent on a list of benchmark cases.

    Args:
        agent: Any object satisfying AgentProtocol.
        cases: List of BenchmarkCase to evaluate on.

    Returns:
        Dict with keys:
          - "per_case": list of per-case metric dicts
          - "report": aggregate report dict from generate_report()
    """
    per_case = [_run_single_case(agent, case) for case in cases]

    # Aggregate metrics
    avg_reward = float(np.mean([r["total_reward"] for r in per_case]))
    avg_calorie_error = float(np.mean([r["calorie_error_pct"] for r in per_case]))
    budget_violation_rate = float(
        np.mean([1.0 if r["budget_violated"] else 0.0 for r in per_case])
    )

    # Diversity: normalize unique_categories by max possible (6 items -> up to 6 categories)
    max_categories = 6.0
    avg_diversity = float(
        np.mean([r["unique_categories"] / max_categories for r in per_case])
    )

    aggregate_score = compute_score(
        calorie_error_pct=avg_calorie_error,
        budget_violation_rate=budget_violation_rate,
        diversity_score=avg_diversity,
        avg_reward=avg_reward,
    )

    report = generate_report(
        aggregate_score=aggregate_score,
        avg_reward=avg_reward,
        calorie_error_pct=avg_calorie_error,
        budget_violation_rate=budget_violation_rate,
        diversity_score=avg_diversity,
    )

    return {
        "per_case": per_case,
        "report": report,
    }
