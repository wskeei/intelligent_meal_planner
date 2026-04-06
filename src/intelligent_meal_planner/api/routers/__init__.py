from .recipes import router as recipes_router
from .meal_plans import router as meal_plans_router
from .meal_chat import router as meal_chat_router
from .auth import router as auth_router
from .weekly_plans import router as weekly_plans_router
from .shopping_lists import router as shopping_lists_router

__all__ = [
    "recipes_router",
    "meal_plans_router",
    "meal_chat_router",
    "auth_router",
    "weekly_plans_router",
    "shopping_lists_router",
]
