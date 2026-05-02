"""
Pydantic 数据模型 - 请求和响应的数据验证
"""

from datetime import date, datetime
from enum import Enum
from typing import Any, List, Literal, Optional

from pydantic import BaseModel, Field, model_validator


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
    cooking_time: int = 15
    description: Optional[str] = None
    ingredients: Optional[List[str]] = None
    instructions: Optional[List[str]] = None

    class Config:
        from_attributes = True


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
    source_session_id: str | None = None
    created_at: datetime
    meals: List[MealItem]
    nutrition: NutritionSummary
    target: UserPreferences
    score: float  # RL 模型评分


class MealPlanHistory(BaseModel):
    """配餐历史"""

    total: int
    items: List[MealPlanResponse]


class NegotiatedMealPlanAlternativeResponse(BaseModel):
    option_key: str
    title: str
    rationale: str
    meal_plan: MealPlanResponse


class NegotiatedMealPlanResponse(BaseModel):
    primary: MealPlanResponse
    alternatives: List[NegotiatedMealPlanAlternativeResponse]


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


class ChatMessage(BaseModel):
    role: str
    content: str
    created_at: Optional[datetime] = None


class MealChatMessageRequest(BaseModel):
    content: str = Field(..., min_length=1)


class MealChatPresentationRequest(BaseModel):
    overlay_state: Literal["hidden", "result"]


class MealChatPresentation(BaseModel):
    phase: str
    overlay_state: str | None = None
    can_generate: bool = False
    has_result_overlay: bool = False


class MealChatSessionResponse(BaseModel):
    session_id: str
    status: str
    messages: List[ChatMessage]
    meal_plan: MealPlanResponse | NegotiatedMealPlanResponse | None = None
    crew_trace: List[dict] = Field(default_factory=list)
    open_questions: List[str] = Field(default_factory=list)
    known_facts: dict = Field(default_factory=dict)
    follow_up_plan: dict | None = None
    profile_snapshot: dict = Field(default_factory=dict)
    preferences_snapshot: dict = Field(default_factory=dict)
    negotiation_options: List[dict] = Field(default_factory=list)
    presentation: MealChatPresentation | None = None


class WeeklyPlanCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    notes: str | None = None


class WeeklyPlanUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    notes: str | None = None


class WeeklyPlanAttachDayRequest(BaseModel):
    plan_date: date
    meal_plan_id: str
    source_session_id: str


class WeeklyPlanDayResponse(BaseModel):
    id: int
    plan_date: date
    source_session_id: str | None = None
    meal_plan_snapshot: dict[str, Any]
    nutrition_snapshot: dict[str, Any] = Field(default_factory=dict)
    completed: bool = False
    completed_at: datetime | None = None


class WeeklyPlanSummaryResponse(BaseModel):
    id: int
    name: str
    notes: str | None = None
    created_at: datetime
    updated_at: datetime
    day_count: int = 0


class WeeklyPlanResponse(BaseModel):
    id: int
    name: str
    notes: str | None = None
    created_at: datetime
    updated_at: datetime
    days: list[WeeklyPlanDayResponse] = Field(default_factory=list)


class ShoppingListGenerateRequest(BaseModel):
    weekly_plan_id: int
    name: str | None = None


class ShoppingListItemCreateRequest(BaseModel):
    ingredient_name: str = Field(..., min_length=1, max_length=200)
    display_amount: str | None = Field(default=None, max_length=100)
    category: str | None = Field(default=None, max_length=100)


class ShoppingListItemUpdateRequest(BaseModel):
    display_amount: str | None = Field(default=None, max_length=100)
    checked: bool | None = None
    category: str | None = Field(default=None, max_length=100)


class ShoppingListItemResponse(BaseModel):
    id: int
    ingredient_name: str
    display_amount: str = ""
    checked: bool = False
    category: str | None = None
    source_kind: str
    sources: list[dict[str, Any]] = Field(default_factory=list)


class ShoppingListSummaryResponse(BaseModel):
    id: int
    weekly_plan_id: int
    name: str
    status: str
    created_at: datetime
    updated_at: datetime
    item_count: int = 0


class ShoppingListResponse(BaseModel):
    id: int
    weekly_plan_id: int
    name: str
    status: str
    created_at: datetime
    updated_at: datetime
    items: list[ShoppingListItemResponse] = Field(default_factory=list)


# ============ 摄入追踪 ============


class IntakeRecordCreate(BaseModel):
    date: date
    meal_type: str = Field(..., pattern="^(breakfast|lunch|dinner|snack)$")
    recipe_id: Optional[int] = None
    custom_food_name: Optional[str] = Field(default=None, max_length=100)
    actual_calories: Optional[float] = None
    actual_protein: Optional[float] = None
    actual_carbs: Optional[float] = None
    actual_fat: Optional[float] = None
    portion_size: float = Field(default=1.0, gt=0, le=10)
    rating: Optional[int] = Field(default=None, ge=1, le=5)
    note: Optional[str] = None

    @model_validator(mode="after")
    def validate_source(self):
        if not self.recipe_id and not self.custom_food_name:
            raise ValueError("Either recipe_id or custom_food_name is required")
        return self


class IntakeRecordUpdate(BaseModel):
    portion_size: Optional[float] = Field(default=None, gt=0, le=10)
    rating: Optional[int] = Field(default=None, ge=1, le=5)
    note: Optional[str] = None


class QuickLogCreate(BaseModel):
    model_config = {"populate_by_name": True}

    log_date: date = Field(default_factory=date.today, alias="date")
    recipe_id: int
    portion_size: float = Field(default=1.0, gt=0, le=10)
    meal_type: Optional[str] = Field(default=None, pattern="^(breakfast|lunch|dinner|snack)$")


class IntakeRecordResponse(BaseModel):
    id: int
    date: date
    meal_type: str
    recipe_id: Optional[int] = None
    recipe_name: Optional[str] = None
    custom_food_name: Optional[str] = None
    actual_calories: float
    actual_protein: float
    actual_carbs: float
    actual_fat: float
    portion_size: float
    source: str
    source_plan_day_id: Optional[int] = None
    rating: Optional[int] = None
    note: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ConfirmDayResponse(BaseModel):
    synced_count: int
    records: list[IntakeRecordResponse] = Field(default_factory=list)


class CancelConfirmResponse(BaseModel):
    success: bool = True


class DailyIntakeSummary(BaseModel):
    date: date
    total_calories: float = 0
    total_protein: float = 0
    total_carbs: float = 0
    total_fat: float = 0
    meal_count: int = 0
    records: list[IntakeRecordResponse] = Field(default_factory=list)


# ============ 营养看板 ============


class NutritionTarget(BaseModel):
    calories: float
    protein: float
    carbs: float
    fat: float


class DailyDashboardResponse(BaseModel):
    date: date
    target: NutritionTarget
    actual: NutritionTarget
    remaining: NutritionTarget
    meals_logged: int
    meals_planned: int = 3
    completion_rate: float


class WeeklySummaryDay(BaseModel):
    date: date
    calories: float = 0
    protein: float = 0
    carbs: float = 0
    fat: float = 0
    meal_count: int = 0
    on_target: bool = False


class WeeklyDashboardResponse(BaseModel):
    days: list[WeeklySummaryDay] = Field(default_factory=list)
    avg_calories: float = 0
    avg_protein: float = 0
    avg_carbs: float = 0
    avg_fat: float = 0
    target_adherence_rate: float = 0


class WeightLogCreate(BaseModel):
    date: date
    weight: float = Field(..., gt=20, le=300)
    body_fat_pct: Optional[float] = Field(default=None, gt=0, le=60)
    note: Optional[str] = None


class WeightLogResponse(BaseModel):
    id: int
    date: date
    weight: float
    body_fat_pct: Optional[float] = None
    note: Optional[str] = None

    class Config:
        from_attributes = True


class ReminderResponse(BaseModel):
    id: int
    type: str
    title: str
    message: str
    severity: str
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True


class TrendPoint(BaseModel):
    period: str
    avg_calories: float = 0
    avg_protein: float = 0
    avg_carbs: float = 0
    avg_fat: float = 0
    adherence_rate: float = 0


class ReportRequest(BaseModel):
    report_type: str = Field(default="weekly", pattern="^(weekly|monthly)$")
    start_date: Optional[date] = None


class ReportResponse(BaseModel):
    report_type: str
    html: str
    generated_at: datetime


class InsightResponse(BaseModel):
    insight: str
    generated_at: datetime
