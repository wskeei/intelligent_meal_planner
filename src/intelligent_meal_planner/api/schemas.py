"""
Pydantic 数据模型 - 请求和响应的数据验证
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class HealthGoal(str, Enum):
    """健康目标枚举"""
    LOSE_WEIGHT = "lose_weight"
    GAIN_MUSCLE = "gain_muscle"
    MAINTAIN = "maintain"
    HEALTHY = "healthy"


# ============ 用户相关 ============

class UserPreferences(BaseModel):
    """用户偏好设置"""
    health_goal: HealthGoal = HealthGoal.HEALTHY
    target_calories: int = Field(default=2000, ge=1200, le=4000)
    target_protein: int = Field(default=100, ge=30, le=300)
    target_carbs: int = Field(default=250, ge=50, le=500)
    target_fat: int = Field(default=60, ge=20, le=200)
    max_budget: float = Field(default=50.0, ge=10, le=200)
    disliked_foods: List[str] = Field(default_factory=list)
    preferred_tags: List[str] = Field(default_factory=list)


class UserCreate(BaseModel):
    """创建用户请求"""
    username: str = Field(..., min_length=2, max_length=50)
    preferences: Optional[UserPreferences] = None


class UserResponse(BaseModel):
    """用户响应"""
    id: int
    username: str
    preferences: UserPreferences
    created_at: datetime


# ============ 菜品相关 ============

class RecipeBase(BaseModel):
    """菜品基础信息"""
    id: int
    name: str
    category: str
    calories: float
    protein: float
    carbs: float
    fat: float
    price: float
    tags: List[str]
    meal_type: List[str]
    cooking_time: int
    description: Optional[str] = None


class RecipeListResponse(BaseModel):
    """菜品列表响应"""
    total: int
    items: List[RecipeBase]


class RecipeFilter(BaseModel):
    """菜品筛选条件"""
    meal_type: Optional[str] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    tags: Optional[List[str]] = None
    category: Optional[str] = None
    limit: int = Field(default=50, le=100)
    offset: int = Field(default=0, ge=0)


# ============ 配餐相关 ============

class MealItem(BaseModel):
    """单餐菜品"""
    meal_type: str  # breakfast, lunch, dinner
    recipe_id: int
    recipe_name: str
    calories: float
    protein: float
    carbs: float
    fat: float
    price: float


class NutritionSummary(BaseModel):
    """营养汇总"""
    total_calories: float
    total_protein: float
    total_carbs: float
    total_fat: float
    total_price: float
    calories_achievement: float  # 百分比
    protein_achievement: float
    budget_usage: float


class MealPlanRequest(BaseModel):
    """配餐请求"""
    user_id: Optional[int] = None
    preferences: Optional[UserPreferences] = None
    use_agent: bool = Field(default=False, description="是否使用 Agent 对话模式")
    user_message: Optional[str] = Field(None, description="用户自然语言需求")


class MealPlanResponse(BaseModel):
    """配餐响应"""
    id: str
    created_at: datetime
    meals: List[MealItem]
    nutrition: NutritionSummary
    target: UserPreferences
    score: float  # RL 模型评分


class MealPlanHistory(BaseModel):
    """配餐历史"""
    total: int
    items: List[MealPlanResponse]


# ============ 通用响应 ============

class APIResponse(BaseModel):
    """通用 API 响应"""
    success: bool
    message: str
    data: Optional[dict] = None


class ErrorResponse(BaseModel):
    """错误响应"""
    success: bool = False
    error_code: str
    message: str
    detail: Optional[str] = None