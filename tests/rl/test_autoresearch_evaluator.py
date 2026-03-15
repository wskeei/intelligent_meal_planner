"""Tests for autoresearch evaluator module."""

import pytest
import numpy as np

from intelligent_meal_planner.rl.autoresearch.benchmark import (
    BenchmarkCase,
    get_default_benchmark_cases,
)
from intelligent_meal_planner.rl.autoresearch.evaluator import (
    AgentProtocol,
    evaluate_agent,
)


class FakeDeterministicAgent:
    """A fake agent that always picks the first valid action. Satisfies AgentProtocol."""

    def select_action(
        self,
        state: np.ndarray,
        action_mask: np.ndarray,
        step: int,
        deterministic: bool = True,
    ) -> int:
        valid_actions = np.where(action_mask)[0]
        if len(valid_actions) == 0:
            return 0
        return int(valid_actions[0])


class TestEvaluator:
    """Test evaluator runs all benchmark cases and returns proper results."""

    def test_evaluator_runs_all_cases(self):
        agent = FakeDeterministicAgent()
        cases = get_default_benchmark_cases()
        results = evaluate_agent(agent, cases)

        assert len(results["per_case"]) == len(cases)
        for case_result in results["per_case"]:
            assert "case_name" in case_result
            assert "total_reward" in case_result
            assert "total_calories" in case_result
            assert "total_cost" in case_result
            assert "unique_categories" in case_result

    def test_evaluator_returns_aggregate_report(self):
        agent = FakeDeterministicAgent()
        cases = get_default_benchmark_cases()
        results = evaluate_agent(agent, cases)

        assert "report" in results
        report = results["report"]
        assert "aggregate_score" in report
        assert "avg_reward" in report
        assert "calorie_error_pct" in report
        assert "budget_violation_rate" in report
        assert "diversity_score" in report

    def test_evaluator_with_single_case(self):
        agent = FakeDeterministicAgent()
        case = BenchmarkCase(
            name="test_single",
            target_calories=2000.0,
            target_protein=100.0,
            target_carbs=250.0,
            target_fat=65.0,
            budget_limit=100.0,
        )
        results = evaluate_agent(agent, [case])

        assert len(results["per_case"]) == 1
        assert results["per_case"][0]["case_name"] == "test_single"

    def test_evaluator_rewards_are_numeric(self):
        agent = FakeDeterministicAgent()
        cases = get_default_benchmark_cases()[:2]
        results = evaluate_agent(agent, cases)

        for case_result in results["per_case"]:
            assert isinstance(case_result["total_reward"], (int, float))
            assert isinstance(case_result["total_calories"], (int, float))
            assert isinstance(case_result["total_cost"], (int, float))

    def test_agent_protocol_compliance(self):
        """Verify FakeDeterministicAgent satisfies the protocol."""
        agent = FakeDeterministicAgent()
        mask = np.array([False, True, True, False, True])
        state = np.zeros(13, dtype=np.float32)
        action = agent.select_action(state, mask, step=0, deterministic=True)
        assert action == 1  # first valid index
