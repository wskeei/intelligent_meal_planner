# tests/meal_chat_v2/test_rl_tool.py
import json
import pytest
from unittest.mock import patch, MagicMock

from intelligent_meal_planner.meal_chat.tools.rl_planning_tool import (
    dqn_meal_planning_tool,
    create_meal_plan_dict,
)


class TestRLPlanningTool:
    @patch("intelligent_meal_planner.meal_chat.tools.rl_planning_tool.RLModelTool")
    def test_tool_returns_json(self, mock_rl_tool_class):
        """测试工具返回 JSON 字符串"""
        mock_tool = MagicMock()
        mock_tool._run.return_value = json.dumps({
            "status": "ok",
            "meal_plan": {"breakfast_0": 1},
            "metrics": {"total_calories": 1800},
        })
        mock_rl_tool_class.return_value = mock_tool

        result = dqn_meal_planning_tool.run(
            health_goal="lose_weight",
            budget=80.0,
            disliked_foods=["香菜"],
            preferred_tags=["清淡"],
            target_calories=1800,
            target_protein=100,
            target_carbs=180,
            target_fat=55,
        )

        # 验证返回的是 JSON 字符串
        assert isinstance(result, str)
        data = json.loads(result)
        assert data["status"] == "ok"

    @patch("intelligent_meal_planner.meal_chat.tools.rl_planning_tool.RLModelTool")
    def test_create_meal_plan_dict(self, mock_rl_tool_class):
        """测试便捷函数返回字典"""
        mock_tool = MagicMock()
        mock_tool._run.return_value = json.dumps({
            "status": "ok",
            "meal_plan": {"breakfast_0": 1, "lunch_0": 2, "dinner_0": 3},
            "metrics": {
                "total_calories": 1800,
                "total_cost": 75.0,
            },
        })
        mock_rl_tool_class.return_value = mock_tool

        result = create_meal_plan_dict(
            health_goal="lose_weight",
            budget=80.0,
            disliked_foods=[],
            preferred_tags=[],
            target_calories=1800,
            target_protein=100,
            target_carbs=180,
            target_fat=55,
        )

        # 验证返回的是字典
        assert isinstance(result, dict)
        assert result["status"] == "ok"
        assert "meal_plan" in result

    @patch("intelligent_meal_planner.meal_chat.tools.rl_planning_tool.RLModelTool")
    def test_tool_passes_correct_params(self, mock_rl_tool_class):
        """测试参数正确传递"""
        mock_tool = MagicMock()
        mock_tool._run.return_value = "{}"
        mock_rl_tool_class.return_value = mock_tool

        dqn_meal_planning_tool.run(
            health_goal="gain_muscle",
            budget=100.0,
            disliked_foods=["内脏", "香菜"],
            preferred_tags=["高蛋白"],
            target_calories=2200,
            target_protein=150,
            target_carbs=250,
            target_fat=70,
        )

        # 验证参数传递
        call_args = mock_tool._run.call_args
        assert call_args.kwargs["target_calories"] == 2200
        assert call_args.kwargs["target_protein"] == 150
        assert call_args.kwargs["max_budget"] == 100.0
        assert "内脏" in call_args.kwargs["disliked_ingredients"]
