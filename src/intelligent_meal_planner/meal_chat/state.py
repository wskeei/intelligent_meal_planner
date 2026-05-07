# src/intelligent_meal_planner/meal_chat/state.py
from typing import Literal
from pydantic import BaseModel, Field
from datetime import datetime


class MessageTurn(BaseModel):
    """单轮对话记录"""

    role: Literal["user", "assistant"]
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ConversationState(BaseModel):
    """对话状态 - CrewAI Flow 的状态管理"""

    # 会话基础信息 (默认值用于 Flow 初始化)
    session_id: str = Field(default="", description="会话唯一标识")
    user_id: str = Field(default="", description="用户 ID")
    turn_count: int = Field(default=0, description="对话轮数")

    # 用户输入 (通过 kickoff 传入)
    user_message: str = Field(default="", description="当前用户消息")

    # 当前上下文
    recent_messages: list[MessageTurn] = Field(
        default_factory=list,
        description="最近 N 轮对话历史",
    )

    current_phase: Literal[
        "discovering",
        "planning_ready",
        "planning",
        "explaining",
        "adjusting",
    ] = Field(
        default="discovering",
        description="当前对话阶段",
    )

    # 收集到的信息
    collected_profile: dict = Field(
        default_factory=dict,
        description="收集到的用户档案信息",
    )

    collected_preferences: dict = Field(
        default_factory=dict,
        description="收集到的用户偏好信息",
    )

    # 配餐结果
    current_meal_plan: dict | None = Field(
        default=None,
        description="当前配餐方案",
    )

    # 意图分析缓存
    last_intent: str = Field(default="", description="最近识别的意图")
    last_confidence: float = Field(default=0.0, description="最近的置信度")

    def add_message(self, role: str, content: str) -> None:
        """添加消息到历史记录"""
        self.recent_messages.append(
            MessageTurn(role=role, content=content)
        )
        # 保留最近 10 轮对话
        if len(self.recent_messages) > 20:  # 10 轮 = 20 条消息
            self.recent_messages = self.recent_messages[-20:]
        self.turn_count += 1

    def get_context_for_llm(self, max_turns: int = 5) -> list[dict]:
        """获取用于 LLM 的上下文"""
        recent = self.recent_messages[-max_turns * 2:]  # 每轮 2 条消息
        return [
            {"role": msg.role, "content": msg.content}
            for msg in recent
        ]

    def is_profile_complete(self) -> bool:
        """检查档案信息是否完整"""
        required = ["gender", "age", "height", "weight", "activity_level"]
        return all(
            self.collected_profile.get(field) is not None
            for field in required
        )

    def is_preferences_complete(self) -> bool:
        """检查偏好信息是否完整"""
        required = ["health_goal", "budget"]
        return all(
            self.collected_preferences.get(field) is not None
            for field in required
        )

    def is_ready_for_planning(self) -> bool:
        """检查是否可以生成配餐方案"""
        return self.is_profile_complete() and self.is_preferences_complete()

    def merge_updates(
        self,
        profile_updates: dict | None = None,
        preference_updates: dict | None = None,
    ) -> None:
        """合并更新到状态"""
        if profile_updates:
            self.collected_profile.update(profile_updates)
        if preference_updates:
            self.collected_preferences.update(preference_updates)
