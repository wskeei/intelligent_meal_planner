# src/intelligent_meal_planner/meal_chat/models/planning.py
from pydantic import BaseModel, Field


class PlanningResult(BaseModel):
    """配餐方案生成结果"""

    meal_plan: dict = Field(
        default_factory=dict,
        description="RL 生成的配餐方案",
    )

    target_ranges: dict = Field(
        default_factory=dict,
        description="营养目标范围",
    )

    explanation: str = Field(
        default="",
        description="AI 生成的方案解读",
    )

    highlights: list[str] = Field(
        default_factory=list,
        description="方案亮点列表",
    )

    alternatives: list[dict] | None = Field(
        default=None,
        description="备选方案列表（如果有）",
    )

    total_cost: float = Field(
        default=0.0,
        description="方案总花费",
    )

    total_calories: int = Field(
        default=0,
        description="方案总热量",
    )

    status: str = Field(
        default="ok",
        description="生成状态：ok, budget_infeasible, error",
    )
