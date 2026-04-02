"""
Deprecated compatibility exports for the removed single-turn CrewAI runtime.

Runtime meal planning now lives in the conversational meal-chat flow.
"""

from .user_profiler import UserProfilerAgent
from .rl_chef import RLChefAgent
from .crew import MealPlanningCrew

__all__ = ['UserProfilerAgent', 'RLChefAgent', 'MealPlanningCrew']
