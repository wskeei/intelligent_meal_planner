"""Deterministic evaluator for trained DQN checkpoints.

Runs an agent through a set of benchmark cases using MealPlanningEnv in
evaluation (non-training) mode and collects per-case metrics.

Supports dual evaluation: closed (original recipes) + open (with custom recipes).
"""

import io
import contextlib
import numpy as np
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable

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


def _run_single_case(
    agent: AgentProtocol,
    case: BenchmarkCase,
    price_scale: float = 1.0,
    budget_scale: float = 1.0,
    custom_recipes: Optional[List[Dict]] = None,
) -> Dict[str, Any]:
    """Run one benchmark case and return per-case metrics."""
    scaled_budget = case.budget_limit * budget_scale
    env = MealPlanningEnv(
        target_calories=case.target_calories,
        target_protein=case.target_protein,
        target_carbs=case.target_carbs,
        target_fat=case.target_fat,
        budget_limit=scaled_budget,
        training_mode=False,
        price_scale=price_scale,
        custom_recipes=custom_recipes,
    )

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
        "budget_limit": scaled_budget,
        "unique_categories": len(set(env.selected_categories)),
        "calorie_error_pct": abs(env.total_calories - case.target_calories)
        / case.target_calories
        * 100.0,
        "budget_violated": env.total_cost > scaled_budget,
    }


def evaluate_agent(
    agent: AgentProtocol,
    cases: List[BenchmarkCase],
    price_scale: float = 1.0,
    budget_scale: float = 1.0,
    custom_recipes: Optional[List[Dict]] = None,
) -> Dict[str, Any]:
    """Evaluate an agent on a list of benchmark cases."""
    per_case = [
        _run_single_case(agent, case, price_scale=price_scale,
                         budget_scale=budget_scale, custom_recipes=custom_recipes)
        for case in cases
    ]

    avg_reward = float(np.mean([r["total_reward"] for r in per_case]))
    avg_calorie_error = float(np.mean([r["calorie_error_pct"] for r in per_case]))
    budget_violation_rate = float(
        np.mean([1.0 if r["budget_violated"] else 0.0 for r in per_case])
    )
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
        aggregate_score=aggregate_score, avg_reward=avg_reward,
        calorie_error_pct=avg_calorie_error,
        budget_violation_rate=budget_violation_rate,
        diversity_score=avg_diversity,
    )
    return {"per_case": per_case, "report": report}


def evaluate_agent_dual(
    agent: AgentProtocol,
    cases: List[BenchmarkCase],
    price_scale: float = 1.0,
    budget_scale: float = 1.0,
    custom_recipes: Optional[List[Dict]] = None,
) -> Dict[str, Any]:
    """Dual evaluation: closed (original only) + open (with custom recipes + scales).

    Prevents gaming by ensuring 50% of the score comes from a fixed evaluation.
    """
    closed_result = evaluate_agent(
        agent, cases, price_scale=1.0, budget_scale=1.0, custom_recipes=None,
    )
    closed_score = closed_result["report"]["aggregate_score"]

    open_result = evaluate_agent(
        agent, cases, price_scale=price_scale, budget_scale=budget_scale,
        custom_recipes=custom_recipes,
    )
    open_score = open_result["report"]["aggregate_score"]

    final_score = 0.5 * closed_score + 0.5 * open_score

    return {
        "closed_result": closed_result,
        "open_result": open_result,
        "per_case": closed_result["per_case"],
        "report": {
            "aggregate_score": final_score,
            "closed_score": closed_score,
            "open_score": open_score,
            "avg_reward": closed_result["report"]["avg_reward"],
            "calorie_error_pct": closed_result["report"]["calorie_error_pct"],
            "budget_violation_rate": closed_result["report"]["budget_violation_rate"],
            "diversity_score": closed_result["report"]["diversity_score"],
        },
    }
