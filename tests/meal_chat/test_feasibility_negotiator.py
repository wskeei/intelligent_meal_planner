from intelligent_meal_planner.meal_chat.feasibility_negotiator import (
    build_negotiation_result,
)
from intelligent_meal_planner.meal_chat.session_schema import TargetRanges


def test_build_negotiation_result_returns_two_options_when_budget_is_tight():
    ranges = TargetRanges(
        calories_min=1700,
        calories_max=1900,
        protein_min=110,
        protein_max=140,
        carbs_min=130,
        carbs_max=210,
        fat_min=40,
        fat_max=65,
        strategy="fat_loss",
    )

    result = build_negotiation_result(budget=100, target_ranges=ranges)

    assert result.phase == "negotiating"
    assert len(result.options) == 2
    assert {option.key for option in result.options} == {
        "budget_cut",
        "protein_priority",
    }
    assert "最低建议预算" in result.explanation


def test_build_negotiation_result_accepts_budget_when_ranges_are_feasible():
    ranges = TargetRanges(
        calories_min=1500,
        calories_max=1800,
        protein_min=60,
        protein_max=80,
        carbs_min=120,
        carbs_max=220,
        fat_min=35,
        fat_max=60,
        strategy="balanced",
    )

    result = build_negotiation_result(budget=150, target_ranges=ranges)

    assert result.phase == "planning"
    assert result.options == []
