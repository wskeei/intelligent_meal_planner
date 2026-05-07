# src/intelligent_meal_planner/meal_chat/models/conversation.py
from typing import Literal
from pydantic import BaseModel, Field


class ConversationResult(BaseModel):
    """对话生成结果"""

    assistant_message: str = Field(
        description="AI 生成的回复内容",
    )

    needs_clarification: bool = Field(
        default=False,
        description="是否需要进一步澄清",
    )

    clarification_questions: list[str] = Field(
        default_factory=list,
        description="需要澄清的问题列表",
    )

    suggested_phase: Literal[
        "discovering",
        "planning_ready",
        "planning",
        "explaining",
        "adjusting",
    ] = Field(
        default="discovering",
        description="建议的下一阶段",
    )

    should_generate_plan: bool = Field(
        default=False,
        description="是否应该生成配餐方案",
    )
