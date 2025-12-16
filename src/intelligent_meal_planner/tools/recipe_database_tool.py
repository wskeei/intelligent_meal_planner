"""
菜品数据库工具 - 用于查询和过滤菜品信息

这个工具提供了多种方式来查询菜品数据库：
1. 根据菜品ID获取详细信息
2. 根据餐次类型筛选菜品
3. 根据价格范围筛选菜品
4. 根据标签筛选菜品
5. 获取所有菜品列表
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional


class RecipeDatabaseTool:
    """
    菜品数据库查询工具
    
    功能：
    - 根据ID查询菜品
    - 根据餐次筛选（早餐/午餐/晚餐）
    - 根据价格筛选
    - 根据标签筛选
    """
    
    def __init__(self):
        """初始化工具，加载菜品数据库"""
        self.name = "菜品数据库查询工具"
        self.description = (
            "用于查询菜品数据库的工具。可以："
            "1. 根据菜品ID获取详细信息"
            "2. 根据餐次类型（breakfast/lunch/dinner）筛选菜品"
            "3. 根据价格范围筛选菜品"
            "4. 根据标签筛选菜品（如'低卡'、'高蛋白'等）"
            "5. 获取所有菜品的简要信息"
        )
    
        
        # 获取数据文件路径
        current_dir = Path(__file__).parent.parent
        data_path = current_dir / "data" / "recipes.json"
        
        # 加载菜品数据
        with open(data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # 数据格式是 {"recipes": [...]}
            self.recipes = data.get('recipes', [])
        
        print(f"[OK] 已加载 {len(self.recipes)} 道菜品")
    
    def _run(self, 
             recipe_ids: Optional[List[int]] = None,
             meal_type: Optional[str] = None,
             min_price: Optional[float] = None,
             max_price: Optional[float] = None,
             tags: Optional[List[str]] = None,
             exclude_tags: Optional[List[str]] = None,
             limit: Optional[int] = None) -> str:
        """
        查询菜品数据库
        
        参数：
            recipe_ids: 菜品ID列表，如 [1, 5, 10]
            meal_type: 餐次类型，可选 "breakfast", "lunch", "dinner"
            min_price: 最低价格
            max_price: 最高价格
            tags: 必须包含的标签列表
            exclude_tags: 必须排除的标签列表
            limit: 返回结果的最大数量
            
        返回：
            JSON格式的菜品信息字符串
        """
        
        results = []
        
        # 如果指定了ID列表，直接返回对应的菜品
        if recipe_ids:
            for recipe_id in recipe_ids:
                recipe = self._get_recipe_by_id(recipe_id)
                if recipe:
                    results.append(recipe)
        else:
            # 否则根据条件筛选
            for recipe in self.recipes:
                # 餐次筛选
                if meal_type and meal_type not in recipe.get('meal_type', []):
                    continue
                
                # 价格筛选
                price = recipe.get('price', 0)
                if min_price is not None and price < min_price:
                    continue
                if max_price is not None and price > max_price:
                    continue
                
                # 标签筛选
                recipe_tags = recipe.get('tags', [])
                if tags and not all(tag in recipe_tags for tag in tags):
                    continue
                if exclude_tags and any(tag in recipe_tags for tag in exclude_tags):
                    continue
                
                results.append(recipe)
        
        # 限制返回数量
        if limit:
            results = results[:limit]
        
        # 格式化输出
        return self._format_results(results)
    
    def _get_recipe_by_id(self, recipe_id: int) -> Optional[Dict[str, Any]]:
        """根据ID获取菜品"""
        for recipe in self.recipes:
            if recipe['id'] == recipe_id:
                return recipe
        return None
    
    def _format_results(self, results: List[Dict[str, Any]]) -> str:
        """格式化查询结果为易读的字符串"""
        if not results:
            return "未找到符合条件的菜品"
        
        output = f"找到 {len(results)} 道菜品：\n\n"
        
        for recipe in results:
            output += f"【{recipe['id']}】{recipe['name']}\n"
            output += f"  分类：{recipe.get('category', '未分类')}\n"
            output += f"  价格：¥{recipe.get('price', 0)}\n"
            output += f"  营养：热量{recipe.get('calories', 0)}kcal | "
            output += f"蛋白质{recipe.get('protein', 0)}g | "
            output += f"碳水{recipe.get('carbs', 0)}g | "
            output += f"脂肪{recipe.get('fat', 0)}g\n"
            output += f"  适合餐次：{', '.join(recipe.get('meal_type', []))}\n"
            output += f"  标签：{', '.join(recipe.get('tags', []))}\n"
            output += f"  烹饪时间：{recipe.get('cooking_time', 0)}分钟\n"
            if 'description' in recipe:
                output += f"  描述：{recipe['description']}\n"
            output += "-" * 50 + "\n"
        
        return output
    
    def get_all_recipe_ids(self, meal_type: Optional[str] = None) -> List[int]:
        """
        获取所有菜品ID（可选按餐次筛选）
        
        参数：
            meal_type: 餐次类型，可选 "breakfast", "lunch", "dinner"
            
        返回：
            菜品ID列表
        """
        ids = []
        for recipe in self.recipes:
            if meal_type is None or meal_type in recipe.get('meal_type', []):
                ids.append(recipe['id'])
        return ids
    
    def get_recipe_summary(self, recipe_ids: List[int]) -> Dict[str, Any]:
        """
        获取多道菜品的营养汇总
        
        参数：
            recipe_ids: 菜品ID列表
            
        返回：
            包含总营养信息的字典
        """
        total = {
            'calories': 0,
            'protein': 0,
            'carbs': 0,
            'fat': 0,
            'price': 0,
            'recipes': []
        }
        
        for recipe_id in recipe_ids:
            recipe = self._get_recipe_by_id(recipe_id)
            if recipe:
                total['calories'] += recipe['calories']
                total['protein'] += recipe['protein']
                total['carbs'] += recipe['carbs']
                total['fat'] += recipe['fat']
                total['price'] += recipe['price']
                total['recipes'].append({
                    'id': recipe['id'],
                    'name': recipe['name'],
                    'category': recipe['category']
                })
        
        return total


# 创建工具实例（供外部导入使用）
recipe_db_tool = RecipeDatabaseTool()