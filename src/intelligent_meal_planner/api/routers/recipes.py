from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_, text
from typing import List, Optional

from ...db.database import get_db
from ...db import models
from ..schemas import RecipeBase, RecipeListResponse

router = APIRouter(prefix="/recipes", tags=["菜品管理"])

@router.get("", response_model=RecipeListResponse)
async def get_recipes(
    search: Optional[str] = Query(None, description="搜索关键词(名称)"),
    meal_type: Optional[str] = Query(None, description="餐次"),
    category: Optional[str] = Query(None),
    min_price: Optional[float] = Query(None),
    max_price: Optional[float] = Query(None),
    min_calories: Optional[float] = Query(None),
    max_calories: Optional[float] = Query(None),
    limit: int = Query(20, le=100),
    offset: int = 0,
    db: Session = Depends(get_db)
):
    query = db.query(models.Recipe)
    
    if search:
        query = query.filter(models.Recipe.name.ilike(f"%{search}%"))
    
    if meal_type:
        # JSON filter is tricky in SQLite with SQLAlchemy abstractly, 
        # but simple string check might work for simple cases or use detailed logic.
        # For SQLite, we can check if string exists in the JSON string representation
        # Ideally, use a proper search engine or Postgres. 
        # Hack for SQLite JSON list:
        query = query.filter(models.Recipe.meal_type.like(f'%"{meal_type}"%'))
        
    if category:
        query = query.filter(models.Recipe.category == category)
        
    if min_price is not None:
        query = query.filter(models.Recipe.price >= min_price)
    if max_price is not None:
        query = query.filter(models.Recipe.price <= max_price)
        
    if min_calories is not None:
        query = query.filter(models.Recipe.calories >= min_calories)
    if max_calories is not None:
        query = query.filter(models.Recipe.calories <= max_calories)
        
    total = query.count()
    items = query.offset(offset).limit(limit).all()
    
    return RecipeListResponse(total=total, items=items)

@router.get("/categories", response_model=List[str])
async def get_categories(db: Session = Depends(get_db)):
    results = db.query(models.Recipe.category).distinct().all()
    return [r[0] for r in results]

@router.get("/{recipe_id}", response_model=RecipeBase)
async def get_recipe(recipe_id: int, db: Session = Depends(get_db)):
    recipe = db.query(models.Recipe).filter(models.Recipe.id == recipe_id).first()
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return recipe