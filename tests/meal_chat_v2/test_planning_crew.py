# tests/meal_chat_v2/test_planning_crew.py
import pytest
from unittest.mock import patch, MagicMock

from intelligent_meal_planner.meal_chat.crews.planning_crew import (
    PlanningCrew,
    calculate_target_ranges,
    create_requirements_reviewer_agent,
    create_nutrition_planner_agent,
)


def create_mock_llm():
    """Create a mock LLM that satisfies CrewAI's Agent requirements."""
    mock_llm = MagicMock()
    mock_llm.model = "deepseek/deepseek-chat"
    return mock_llm


class TestCalculateTargetRanges:
    def test_calculate_for_weight_loss(self):
        profile = {
            "gender": "male",
            "age": 28,
            "height_cm": 175,
            "weight_kg": 72,
            "activity_level": "moderate",
        }
        ranges = calculate_target_ranges(profile, "lose_weight")

        # 减脂应该有热量缺口
        assert ranges["calories_max"] < ranges["tdee"] * 1.05
        assert ranges["protein_min"] > 0
        assert "bmr" in ranges

    def test_calculate_for_muscle_gain(self):
        profile = {
            "gender": "male",
            "age": 25,
            "height_cm": 180,
            "weight_kg": 70,
            "activity_level": "active",
        }
        ranges = calculate_target_ranges(profile, "gain_muscle")

        # 增肌应该有热量盈余
        assert ranges["calories_min"] > ranges["tdee"] * 0.9
        # 增肌蛋白质需求更高
        assert ranges["protein_max"] >= profile["weight_kg"] * 1.8


class TestPlanningCrewAgents:
    @patch("intelligent_meal_planner.meal_chat.crews.planning_crew.get_planning_llm")
    def test_create_reviewer_agent(self, mock_llm):
        mock_llm.return_value = create_mock_llm()
        agent = create_requirements_reviewer_agent()
        assert agent.role == "需求审核员"

    @patch("intelligent_meal_planner.meal_chat.crews.planning_crew.get_planning_llm")
    def test_create_planner_agent(self, mock_llm):
        mock_llm.return_value = create_mock_llm()
        agent = create_nutrition_planner_agent()
        assert agent.role == "营养规划师"


class TestPlanningCrew:
    @patch("intelligent_meal_planner.meal_chat.crews.planning_crew.create_meal_plan_dict")
    def test_planning_crew_run_success(self, mock_create_plan):
        mock_create_plan.return_value = {
            "status": "ok",
            "meal_plan": {"breakfast_0": 1, "lunch_0": 2, "dinner_0": 3},
            "metrics": {
                "total_calories": 1800,
                "total_protein": 120,
                "total_cost": 75.0,
                "calories_achievement": 95,
                "protein_achievement": 100,
                "budget_usage": 75,
            },
        }

        crew = PlanningCrew()
        result = crew.run(
            profile={
                "gender": "male",
                "age": 28,
                "height_cm": 175,
                "weight_kg": 72,
                "activity_level": "moderate",
            },
            preferences={
                "health_goal": "lose_weight",
                "budget": 100,
                "disliked_foods": [],
                "preferred_tags": [],
            },
        )

        assert result.status == "ok"
        assert result.total_calories == 1800
        assert len(result.highlights) > 0

    @patch("intelligent_meal_planner.meal_chat.crews.planning_crew.create_meal_plan_dict")
    def test_planning_crew_budget_infeasible(self, mock_create_plan):
        mock_create_plan.return_value = {
            "status": "budget_infeasible",
            "meal_plan": {},
            "metrics": {},
        }

        crew = PlanningCrew()
        result = crew.run(
            profile={
                "gender": "male",
                "age": 28,
                "height_cm": 175,
                "weight_kg": 72,
                "activity_level": "moderate",
            },
            preferences={
                "health_goal": "lose_weight",
                "budget": 30,  # 太低
            },
        )

        assert result.status == "budget_infeasible"
        assert "增加预算" in result.explanation

    @patch("intelligent_meal_planner.meal_chat.crews.planning_crew.create_meal_plan_dict")
    def test_planning_crew_error_handling(self, mock_create_plan):
        mock_create_plan.side_effect = Exception("Model not found")

        crew = PlanningCrew()
        result = crew.run(
            profile={
                "gender": "male",
                "age": 28,
                "height_cm": 175,
                "weight_kg": 72,
                "activity_level": "moderate",
            },
            preferences={
                "health_goal": "lose_weight",
                "budget": 100,
            },
        )

        assert result.status == "error"
        assert "出错" in result.explanation
