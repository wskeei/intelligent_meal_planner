"""
API 路由模块
"""

from .recipes import router as recipes_router
from .meal_plans import router as meal_plans_router

__all__ = ['recipes_router', 'meal_plans_router']