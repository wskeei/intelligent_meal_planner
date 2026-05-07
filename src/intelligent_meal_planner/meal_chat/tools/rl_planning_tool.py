# src/intelligent_meal_planner/meal_chat/tools/rl_planning_tool.py
"""RL 配餐工具 - CrewAI Tool 包装器"""

import json
from typing import Optional

from crewai.tools import tool

from ...tools.rl_model_tool import RLModelTool


@tool("DQN配餐工具")
def dqn_meal_planning_tool(
    health_goal: str,
    budget: float,
    disliked_foods: list[str],
    preferred_tags: list[str],
    target_calories: int,
    target_protein: int,
    target_carbs: int,
    target_fat: int,
) -> str:
    """
    使用强化学习模型生成配餐方案。

    Args:
        health_goal: 健康目标 (lose_weight/gain_muscle/maintain/healthy)
        budget: 每日预算（元）
        disliked_foods: 忌口食材列表
        preferred_tags: 偏好标签列表
        target_calories: 目标热量 (kcal)
        target_protein: 目标蛋白质 (g)
        target_carbs: 目标碳水化合物 (g)
        target_fat: 目标脂肪 (g)

    Returns:
        JSON 字符串，包含配餐方案和营养统计
    """
    rl_tool = RLModelTool()

    result_json = rl_tool._run(
        target_calories=target_calories,
        target_protein=target_protein,
        target_carbs=target_carbs,
        target_fat=target_fat,
        max_budget=budget,
        disliked_ingredients=disliked_foods if disliked_foods else None,
        preferred_tags=preferred_tags if preferred_tags else None,
        strict_budget=True,
    )

    return result_json


def create_meal_plan_dict(
    health_goal: str,
    budget: float,
    disliked_foods: list[str],
    preferred_tags: list[str],
    target_calories: int,
    target_protein: int,
    target_carbs: int,
    target_fat: int,
) -> dict:
    """
    生成配餐方案并返回字典。

    这是一个便捷函数，用于在 Crew 内部调用。
    """
    result_str = dqn_meal_planning_tool.run(
        health_goal=health_goal,
        budget=budget,
        disliked_foods=disliked_foods,
        preferred_tags=preferred_tags,
        target_calories=target_calories,
        target_protein=target_protein,
        target_carbs=target_carbs,
        target_fat=target_fat,
    )
    return json.loads(result_str)
