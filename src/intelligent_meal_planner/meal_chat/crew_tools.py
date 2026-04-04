from __future__ import annotations

import json

from crewai.tools.base_tool import BaseTool
from pydantic import BaseModel, Field


class MealPlanningToolInput(BaseModel):
    health_goal: str = Field(default="healthy")
    budget: float = Field(..., gt=0)
    disliked_foods: list[str] = Field(default_factory=list)
    preferred_tags: list[str] = Field(default_factory=list)
    hidden_targets: dict = Field(default_factory=dict)


class DQNMealPlanningTool(BaseTool):
    name: str = "dqn_meal_planning_tool"
    description: str = "调用 DQN 配餐器，根据预算、目标和饮食偏好生成结构化一日三餐方案。"
    args_schema: type[BaseModel] = MealPlanningToolInput

    def __init__(self, planning_tool):
        super().__init__()
        self._planning_tool = planning_tool

    def _run(
        self,
        health_goal: str,
        budget: float,
        disliked_foods: list[str] | None = None,
        preferred_tags: list[str] | None = None,
        hidden_targets: dict | None = None,
    ) -> str:
        if self._planning_tool is None:
            return json.dumps({"status": "unavailable", "meal_plan": None}, ensure_ascii=False)

        result = self._planning_tool.generate(
            goal=health_goal,
            budget=budget,
            disliked_foods=disliked_foods or [],
            preferred_tags=preferred_tags or [],
            hidden_targets=hidden_targets or {},
        )
        return json.dumps(result, ensure_ascii=False)


def build_dqn_planning_tool(planning_tool):
    if planning_tool is None:
        return None
    return DQNMealPlanningTool(planning_tool=planning_tool)
