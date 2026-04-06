from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    
    # Profile Data
    age = Column(Integer, nullable=True)
    gender = Column(String, nullable=True)
    height = Column(Float, nullable=True)
    weight = Column(Float, nullable=True)
    activity_level = Column(String, nullable=True)
    health_goal = Column(String, default="healthy")

class Recipe(Base):
    __tablename__ = "recipes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    category = Column(String, index=True)
    
    # Nutrition
    calories = Column(Float)
    protein = Column(Float)
    carbs = Column(Float)
    fat = Column(Float)
    
    price = Column(Float)
    cooking_time = Column(Integer)
    
    description = Column(Text, nullable=True)
    tags = Column(JSON)      # Store as JSON list: ["high-protein", "vegan"]
    meal_type = Column(JSON) # Store as JSON list: ["breakfast"]
    
    # New Fields for Detail View
    ingredients = Column(JSON) # List of strings or objects
    instructions = Column(JSON) # List of steps


class MealChatSession(Base):
    __tablename__ = "meal_chat_sessions"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    status = Column(String, nullable=False, default="discovering")
    collected_slots = Column(JSON, nullable=False, default=dict)
    hidden_targets = Column(JSON, nullable=True)
    final_plan = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class MealChatMessage(Base):
    __tablename__ = "meal_chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, ForeignKey("meal_chat_sessions.id"), nullable=False, index=True)
    role = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    stage = Column(String, nullable=False, default="collecting")
    created_at = Column(DateTime, default=datetime.utcnow)


class WeeklyPlan(Base):
    __tablename__ = "weekly_plans"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    days = relationship(
        "WeeklyPlanDay",
        back_populates="weekly_plan",
        cascade="all, delete-orphan",
        order_by="WeeklyPlanDay.plan_date",
    )
    shopping_lists = relationship(
        "ShoppingList",
        back_populates="weekly_plan",
        cascade="all, delete-orphan",
    )


class WeeklyPlanDay(Base):
    __tablename__ = "weekly_plan_days"
    __table_args__ = (
        UniqueConstraint("weekly_plan_id", "plan_date", name="uq_weekly_plan_day_date"),
    )

    id = Column(Integer, primary_key=True, index=True)
    weekly_plan_id = Column(
        Integer, ForeignKey("weekly_plans.id"), nullable=False, index=True
    )
    plan_date = Column(Date, nullable=False, index=True)
    source_session_id = Column(String, nullable=True)
    meal_plan_snapshot = Column(JSON, nullable=False)
    nutrition_snapshot = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    weekly_plan = relationship("WeeklyPlan", back_populates="days")


class ShoppingList(Base):
    __tablename__ = "shopping_lists"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    weekly_plan_id = Column(
        Integer, ForeignKey("weekly_plans.id"), nullable=False, index=True
    )
    name = Column(String, nullable=False)
    status = Column(String, nullable=False, default="active")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    weekly_plan = relationship("WeeklyPlan", back_populates="shopping_lists")
    items = relationship(
        "ShoppingListItem",
        back_populates="shopping_list",
        cascade="all, delete-orphan",
        order_by="ShoppingListItem.id",
    )


class ShoppingListItem(Base):
    __tablename__ = "shopping_list_items"

    id = Column(Integer, primary_key=True, index=True)
    shopping_list_id = Column(
        Integer, ForeignKey("shopping_lists.id"), nullable=False, index=True
    )
    ingredient_name = Column(String, nullable=False, index=True)
    display_amount = Column(String, nullable=True)
    checked = Column(Boolean, nullable=False, default=False)
    category = Column(String, nullable=True)
    source_kind = Column(String, nullable=False, default="weekly-plan")
    source_refs = Column(JSON, nullable=False, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    shopping_list = relationship("ShoppingList", back_populates="items")
