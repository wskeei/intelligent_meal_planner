# src/intelligent_meal_planner/meal_chat/models/memory.py
from pydantic import BaseModel, Field


class MemoryUpdateResult(BaseModel):
    """认知文件更新结果"""

    should_update: bool = Field(
        default=False,
        description="是否应该更新用户认知文件",
    )

    update_reason: str | None = Field(
        default=None,
        description="更新原因说明",
    )

    profile_updates: dict = Field(
        default_factory=dict,
        description="档案更新内容",
    )

    preference_updates: dict = Field(
        default_factory=dict,
        description="偏好更新内容",
    )

    taste_profile_updates: dict = Field(
        default_factory=dict,
        description="口味画像更新内容",
    )

    feedback_to_add: dict | None = Field(
        default=None,
        description="要添加的反馈记录",
    )

    confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="对更新内容的置信度",
    )
