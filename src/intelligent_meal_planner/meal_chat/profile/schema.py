# src/intelligent_meal_planner/meal_chat/profile/schema.py
"""
用户认知文件 Schema

注意：部分字段命名与 Plan 文档有差异，原因如下：
- FeedbackRecord.feedback_date (而非 date): 避免与 Python 内置 date 类型冲突
- GoalHistory.changed_at (而非 date): 同上，且更语义化
- GoalHistory.budget 为 Optional[float]: 支持记录不含预算信息的目标变更
"""

from datetime import date
from pydantic import BaseModel, Field
from typing import Literal


class FeedbackRecord(BaseModel):
    """用户对方案的反馈记录"""

    feedback_date: date = Field(description="反馈日期")
    meal_plan_id: str | None = Field(default=None, description="方案 ID")
    liked_dishes: list[str] = Field(
        default_factory=list,
        description="喜欢的菜品",
    )
    disliked_dishes: list[str] = Field(
        default_factory=list,
        description="不喜欢的菜品",
    )
    comment: str | None = Field(default=None, description="用户评论")


class GoalHistory(BaseModel):
    """目标变化历史"""

    changed_at: date = Field(description="变更日期")
    goal: str = Field(description="健康目标")
    budget: float | None = Field(default=None, description="预算")


class UserProfile(BaseModel):
    """用户认知文件 - 持久化用户偏好和档案"""

    user_id: str = Field(description="用户唯一标识")
    created_at: date = Field(default_factory=date.today)
    updated_at: date = Field(default_factory=date.today)

    # 基础档案
    profile: dict = Field(
        default_factory=lambda: {
            "gender": None,
            "age": None,
            "height_cm": None,
            "weight_kg": None,
            "activity_level": None,
        },
        description="用户生理信息",
    )

    # 饮食偏好
    preferences: dict = Field(
        default_factory=lambda: {
            "health_goal": None,
            "budget_daily": None,
            "disliked_foods": [],
            "allergies": [],
        },
        description="饮食目标和预算",
    )

    # 口味画像
    taste_profile: dict = Field(
        default_factory=lambda: {
            "preferred_styles": [],  # ["家常", "清淡"]
            "disliked_styles": [],  # ["重辣"]
            "favorite_ingredients": [],  # ["鸡肉", "蔬菜"]
            "avoid_ingredients": [],  # ["肥肉", "香菜"]
        },
        description="口味偏好画像",
    )

    # 行为模式
    behavioral_patterns: dict = Field(
        default_factory=lambda: {
            "cooking_frequency": None,  # often/sometimes/rarely
            "eating_out_frequency": None,  # often/sometimes/rarely
            "meal_timing": None,  # regular/irregular
        },
        description="饮食行为模式",
    )

    # 反馈历史
    feedback_history: list[FeedbackRecord] = Field(
        default_factory=list,
        description="历史反馈记录",
    )

    # 目标历史
    goal_history: list[GoalHistory] = Field(
        default_factory=list,
        description="目标变化历史",
    )

    def update_profile(self, updates: dict) -> None:
        """更新档案信息"""
        self.profile.update({k: v for k, v in updates.items() if v is not None})
        self.updated_at = date.today()

    def update_preferences(self, updates: dict) -> None:
        """更新偏好信息"""
        # 特殊处理：如果目标或预算变化，记录历史
        if "health_goal" in updates and updates["health_goal"] != self.preferences.get("health_goal"):
            self.goal_history.append(
                GoalHistory(
                    changed_at=date.today(),
                    goal=updates["health_goal"],
                    budget=updates.get("budget_daily", self.preferences.get("budget_daily", 0)),
                )
            )

        self.preferences.update({k: v for k, v in updates.items() if v is not None})
        self.updated_at = date.today()

    def update_taste_profile(self, updates: dict) -> None:
        """更新口味画像"""
        for key, values in updates.items():
            if key not in self.taste_profile:
                self.taste_profile[key] = []
            if isinstance(values, list):
                # 合并并去重
                existing = set(self.taste_profile.get(key, []))
                self.taste_profile[key] = list(existing | set(values))
            else:
                self.taste_profile[key] = values
        self.updated_at = date.today()

    def add_feedback(self, feedback: FeedbackRecord) -> None:
        """添加反馈记录"""
        self.feedback_history.append(feedback)
        # 保留最近 50 条反馈
        if len(self.feedback_history) > 50:
            self.feedback_history = self.feedback_history[-50:]
        self.updated_at = date.today()

    def get_summary_for_context(self) -> str:
        """生成用于 LLM 上下文的用户画像摘要"""
        parts = []

        if self.profile.get("age"):
            parts.append(f"年龄{self.profile['age']}岁")
        if self.profile.get("height_cm") and self.profile.get("weight_kg"):
            parts.append(f"身高{self.profile['height_cm']}cm，体重{self.profile['weight_kg']}kg")
        if self.preferences.get("health_goal"):
            goal_map = {
                "lose_weight": "减脂",
                "gain_muscle": "增肌",
                "maintain": "维持",
                "healthy": "健康饮食",
            }
            parts.append(f"目标：{goal_map.get(self.preferences['health_goal'], self.preferences['health_goal'])}")
        if self.preferences.get("budget_daily"):
            parts.append(f"预算{self.preferences['budget_daily']}元/天")
        if self.preferences.get("disliked_foods"):
            parts.append(f"忌口：{', '.join(self.preferences['disliked_foods'])}")
        if self.taste_profile.get("preferred_styles"):
            parts.append(f"偏好口味：{', '.join(self.taste_profile['preferred_styles'])}")

        return "，".join(parts) if parts else "新用户，暂无已知信息"
