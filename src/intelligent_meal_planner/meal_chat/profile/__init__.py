# src/intelligent_meal_planner/meal_chat/profile/__init__.py
from .schema import UserProfile, FeedbackRecord, GoalHistory
from .manager import UserProfileManager

__all__ = [
    "UserProfile",
    "FeedbackRecord",
    "GoalHistory",
    "UserProfileManager",
]