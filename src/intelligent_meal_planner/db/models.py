from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, JSON, String, Text
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
    status = Column(String, nullable=False, default="collecting_profile")
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
