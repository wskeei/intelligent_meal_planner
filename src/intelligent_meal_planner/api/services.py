"""
服务层 - 封装业务逻辑
"""

import json
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from pathlib import Path

from .schemas import (
    UserPreferences, MealPlanResponse, MealItem, 
    NutritionSummary, RecipeBase, RecipeFilter
)


class RecipeService:
    """菜品服务"""
    
    def __init__(self):
        data_path = Path(__file__).parent.parent / "data" / "recipes.json"
        with open(data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        self.recipes = data.get('recipes', [])
    
    def get_all(self, filter: RecipeFilter) -> tuple[List[RecipeBase], int]:
        """获取菜品列表"""
        results = []
        for r in self.recipes:
            if filter.meal_type and filter.meal_type not in r.get('meal_type', []):
                continue
            if filter.min_price and r['price'] < filter.min_price:
                continue
            if filter.max_price and r['price'] > filter.max_price:
                continue
            if filter.category and r['category'] != filter.category:
                continue
            if filter.tags and not all(t in r.get('tags', []) for t in filter.tags):
                continue
            results.append(RecipeBase(**r))
        
        total = len(results)
        return results[filter.offset:filter.offset + filter.limit], total
    
    def get_by_id(self, recipe_id: int) -> Optional[RecipeBase]:
        """根据ID获取菜品"""
        for r in self.recipes:
            if r['id'] == recipe_id:
                return RecipeBase(**r)
        return None
    
    def get_by_ids(self, ids: List[int]) -> List[RecipeBase]:
        """批量获取菜品"""
        return [self.get_by_id(i) for i in ids if self.get_by_id(i)]
    
    def get_categories(self) -> List[str]:
        """获取所有分类"""
        return list(set(r['category'] for r in self.recipes))
    
    def get_tags(self) -> List[str]:
        """获取所有标签"""
        tags = set()
        for r in self.recipes:
            tags.update(r.get('tags', []))
        return list(tags)


class MealPlanService:
    """配餐服务"""
    
    def __init__(self):
        self.recipe_service = RecipeService()
        self._history: Dict[str, MealPlanResponse] = {}
    
    def generate_plan(self, preferences: UserPreferences) -> MealPlanResponse:
        """生成配餐方案"""
        try:
            from ..tools.rl_model_tool import create_rl_model_tool
            tool = create_rl_model_tool()
            result = tool._run(
                target_calories=preferences.target_calories,
                target_protein=preferences.target_protein,
                target_carbs=preferences.target_carbs,
                target_fat=preferences.target_fat,
                max_budget=preferences.max_budget
            )
            data = json.loads(result)
            return self._build_response(data, preferences)
        except FileNotFoundError:
            # 模型未找到时使用随机方案
            return self._generate_random_plan(preferences)
    
    def _build_response(self, data: dict, preferences: UserPreferences) -> MealPlanResponse:
        """构建响应"""
        meal_plan = data.get('meal_plan', {})
        metrics = data.get('metrics', {})
        
        meals = []
        meal_names = {'breakfast': '早餐', 'lunch': '午餐', 'dinner': '晚餐'}
        
        for meal_type, recipe_id in meal_plan.items():
            recipe = self.recipe_service.get_by_id(recipe_id)
            if recipe:
                meals.append(MealItem(
                    meal_type=meal_type,
                    recipe_id=recipe.id,
                    recipe_name=recipe.name,
                    calories=recipe.calories,
                    protein=recipe.protein,
                    carbs=recipe.carbs,
                    fat=recipe.fat,
                    price=recipe.price
                ))
        
        nutrition = NutritionSummary(
            total_calories=metrics.get('total_calories', 0),
            total_protein=metrics.get('total_protein', 0),
            total_carbs=metrics.get('total_carbs', 0),
            total_fat=metrics.get('total_fat', 0),
            total_price=metrics.get('total_cost', 0),
            calories_achievement=metrics.get('calories_achievement', 0),
            protein_achievement=metrics.get('protein_achievement', 0),
            budget_usage=metrics.get('budget_usage', 0)
        )
        
        plan_id = str(uuid.uuid4())[:8]
        response = MealPlanResponse(
            id=plan_id,
            created_at=datetime.now(),
            meals=meals,
            nutrition=nutrition,
            target=preferences,
            score=metrics.get('final_reward', 0)
        )
        
        self._history[plan_id] = response
        return response
    
    def _generate_random_plan(self, preferences: UserPreferences) -> MealPlanResponse:
        """生成随机方案（模型不可用时的备选）"""
        import random
        
        meals = []
        total_cal, total_pro, total_carb, total_fat, total_price = 0, 0, 0, 0, 0
        
        for meal_type in ['breakfast', 'lunch', 'dinner']:
            candidates = [r for r in self.recipe_service.recipes 
                         if meal_type in r.get('meal_type', [])]
            if candidates:
                recipe = random.choice(candidates)
                meals.append(MealItem(
                    meal_type=meal_type,
                    recipe_id=recipe['id'],
                    recipe_name=recipe['name'],
                    calories=recipe['calories'],
                    protein=recipe['protein'],
                    carbs=recipe['carbs'],
                    fat=recipe['fat'],
                    price=recipe['price']
                ))
                total_cal += recipe['calories']
                total_pro += recipe['protein']
                total_carb += recipe['carbs']
                total_fat += recipe['fat']
                total_price += recipe['price']
        
        nutrition = NutritionSummary(
            total_calories=total_cal,
            total_protein=total_pro,
            total_carbs=total_carb,
            total_fat=total_fat,
            total_price=total_price,
            calories_achievement=(total_cal / preferences.target_calories) * 100,
            protein_achievement=(total_pro / preferences.target_protein) * 100,
            budget_usage=(total_price / preferences.max_budget) * 100
        )
        
        plan_id = str(uuid.uuid4())[:8]
        return MealPlanResponse(
            id=plan_id,
            created_at=datetime.now(),
            meals=meals,
            nutrition=nutrition,
            target=preferences,
            score=0
        )
    
    def get_history(self, limit: int = 10) -> List[MealPlanResponse]:
        """获取历史记录"""
        items = list(self._history.values())
        return sorted(items, key=lambda x: x.created_at, reverse=True)[:limit]
    
    def get_by_id(self, plan_id: str) -> Optional[MealPlanResponse]:
        """根据ID获取配餐方案"""
        return self._history.get(plan_id)


# 单例服务实例
recipe_service = RecipeService()
meal_plan_service = MealPlanService()