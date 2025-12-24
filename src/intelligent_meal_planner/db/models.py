from sqlalchemy import Boolean, Column, Float, Integer, String, Text, JSON
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
