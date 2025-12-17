"""
菜品相关 API 路由
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List

from ..schemas import RecipeBase, RecipeListResponse, RecipeFilter
from ..services import recipe_service

router = APIRouter(prefix="/recipes", tags=["菜品管理"])


@router.get("", response_model=RecipeListResponse, summary="获取菜品列表")
async def get_recipes(
    meal_type: Optional[str] = Query(None, description="餐次类型: breakfast/lunch/dinner"),
    category: Optional[str] = Query(None, description="菜品分类"),
    min_price: Optional[float] = Query(None, ge=0, description="最低价格"),
    max_price: Optional[float] = Query(None, ge=0, description="最高价格"),
    tags: Optional[str] = Query(None, description="标签，逗号分隔"),
    limit: int = Query(20, ge=1, le=100, description="每页数量"),
    offset: int = Query(0, ge=0, description="偏移量")
):
    """
    获取菜品列表，支持多种筛选条件
    """
    filter = RecipeFilter(
        meal_type=meal_type,
        category=category,
        min_price=min_price,
        max_price=max_price,
        tags=tags.split(",") if tags else None,
        limit=limit,
        offset=offset
    )
    items, total = recipe_service.get_all(filter)
    return RecipeListResponse(total=total, items=items)


@router.get("/categories", response_model=List[str], summary="获取所有分类")
async def get_categories():
    """获取所有菜品分类"""
    return recipe_service.get_categories()


@router.get("/tags", response_model=List[str], summary="获取所有标签")
async def get_tags():
    """获取所有菜品标签"""
    return recipe_service.get_tags()


@router.get("/{recipe_id}", response_model=RecipeBase, summary="获取菜品详情")
async def get_recipe(recipe_id: int):
    """根据ID获取菜品详细信息"""
    recipe = recipe_service.get_by_id(recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="菜品不存在")
    return recipe