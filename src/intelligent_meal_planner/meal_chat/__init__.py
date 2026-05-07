"""
DeepSeek 驱动的多 Agent 对话系统

这是重构后的对话模块，使用 CrewAI Flow 编排多个专业 Agent。
"""

from .flow import MealChatFlow, create_meal_chat_flow
from .state import ConversationState, MessageTurn
from .models import (
    IntentResult,
    ConversationResult,
    PlanningResult,
    MemoryUpdateResult,
)
from .profile.manager import UserProfileManager
from .profile.schema import UserProfile, FeedbackRecord, GoalHistory

__all__ = [
    # Flow
    "MealChatFlow",
    "create_meal_chat_flow",
    # State
    "ConversationState",
    "MessageTurn",
    # Models
    "IntentResult",
    "ConversationResult",
    "PlanningResult",
    "MemoryUpdateResult",
    # Profile
    "UserProfileManager",
    "UserProfile",
    "FeedbackRecord",
    "GoalHistory",
]
