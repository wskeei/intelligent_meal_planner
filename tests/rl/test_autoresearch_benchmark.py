"""Tests for autoresearch benchmark module."""

import pytest
import json

from intelligent_meal_planner.rl.autoresearch.benchmark import (
    BenchmarkCase,
    get_default_benchmark_cases,
    compute_score,
    generate_report,
)


class TestBenchmarkCases:
    """Test that default benchmark contains deterministic cases with required fields."""

    def test_default_cases_not_empty(self):
        cases = get_default_benchmark_cases()
        assert len(cases) > 0

    def test_cases_are_deterministic(self):
        """Calling twice returns identical cases."""
        cases_a = get_default_benchmark_cases()
        cases_b = get_default_benchmark_cases()
        assert len(cases_a) == len(cases_b)
        for a, b in zip(cases_a, cases_b):
            assert a.target_calories == b.target_calories
            assert a.budget_limit == b.budget_limit
            assert a.target_protein == b.target_protein
            assert a.target_carbs == b.target_carbs
            assert a.target_fat == b.target_fat

    def test_cases_have_required_fields(self):
        cases = get_default_benchmark_cases()
        for case in cases:
            assert isinstance(case, BenchmarkCase)
            assert case.target_calories > 0
            assert case.budget_limit > 0
            assert case.target_protein > 0
            assert case.target_carbs > 0
            assert case.target_fat > 0
            assert case.name  # non-empty string


class TestComputeScore:
    """Test score function decreases when errors worsen."""

    def test_perfect_score_higher_than_imperfect(self):
        # Near-perfect metrics
        good = compute_score(
            calorie_error_pct=5.0,
            budget_violation_rate=0.0,
            diversity_score=1.0,
            avg_reward=30.0,
        )
        # Poor metrics
        bad = compute_score(
            calorie_error_pct=50.0,
            budget_violation_rate=0.8,
            diversity_score=0.2,
            avg_reward=5.0,
        )
        assert good > bad

    def test_score_decreases_with_higher_calorie_error(self):
        s1 = compute_score(calorie_error_pct=5.0, budget_violation_rate=0.0, diversity_score=0.8, avg_reward=20.0)
        s2 = compute_score(calorie_error_pct=30.0, budget_violation_rate=0.0, diversity_score=0.8, avg_reward=20.0)
        assert s1 > s2

    def test_score_decreases_with_higher_budget_violation(self):
        s1 = compute_score(calorie_error_pct=10.0, budget_violation_rate=0.0, diversity_score=0.8, avg_reward=20.0)
        s2 = compute_score(calorie_error_pct=10.0, budget_violation_rate=0.5, diversity_score=0.8, avg_reward=20.0)
        assert s1 > s2

    def test_score_is_numeric(self):
        s = compute_score(calorie_error_pct=10.0, budget_violation_rate=0.1, diversity_score=0.7, avg_reward=15.0)
        assert isinstance(s, float)


class TestGenerateReport:
    """Test report serializer returns stable keys."""

    def test_report_has_required_keys(self):
        report = generate_report(
            aggregate_score=75.0,
            avg_reward=20.0,
            calorie_error_pct=8.5,
            budget_violation_rate=0.1,
            diversity_score=0.85,
        )
        required_keys = {
            "aggregate_score",
            "avg_reward",
            "calorie_error_pct",
            "budget_violation_rate",
            "diversity_score",
        }
        assert required_keys.issubset(set(report.keys()))

    def test_report_is_json_serializable(self):
        report = generate_report(
            aggregate_score=75.0,
            avg_reward=20.0,
            calorie_error_pct=8.5,
            budget_violation_rate=0.1,
            diversity_score=0.85,
        )
        serialized = json.dumps(report)
        deserialized = json.loads(serialized)
        assert deserialized == report

    def test_report_values_match_inputs(self):
        report = generate_report(
            aggregate_score=75.0,
            avg_reward=20.0,
            calorie_error_pct=8.5,
            budget_violation_rate=0.1,
            diversity_score=0.85,
        )
        assert report["aggregate_score"] == 75.0
        assert report["avg_reward"] == 20.0
        assert report["calorie_error_pct"] == 8.5
        assert report["budget_violation_rate"] == 0.1
        assert report["diversity_score"] == 0.85
