# src/intelligent_meal_planner/meal_chat/models/intent.py
from typing import Literal
from pydantic import BaseModel, Field


class IntentResult(BaseModel):
    """意图理解结果"""

    intent: Literal[
        "provide_info",
        "ask_question",
        "request_plan",
        "adjust_plan",
        "chat",
        "complaint",
    ] = Field(description="用户意图类型")

    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="意图识别置信度",
    )

    context_summary: str = Field(
        default="",
        description="对话上下文摘要",
    )

    profile_updates: dict = Field(
        default_factory=dict,
        description="提取到的用户档案更新",
    )

    preference_updates: dict = Field(
        default_factory=dict,
        description="提取到的用户偏好更新",
    )

    question_topic: str | None = Field(
        default=None,
        description="如果是提问，问题的主题",
    )

    adjustment_request: dict | None = Field(
        default=None,
        description="如果是调整请求，调整的内容",
    )

    ready_for_planning: bool = Field(
        default=False,
        description="信息是否足够生成配餐方案",
    )
