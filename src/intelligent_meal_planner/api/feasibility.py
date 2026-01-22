"""
可行性计算服务 - 计算给定预算下的最大可达营养值
"""

import json
from typing import Dict, List, Tuple
from pathlib import Path
from pydantic import BaseModel


class FeasibilityResult(BaseModel):
    """可行性检查结果"""
    budget: float
    max_calories: int
    max_protein: int
    max_carbs: int
    max_fat: int
    # 各指标可达性百分比
    calories_feasibility: float = 100.0
    protein_feasibility: float = 100.0
    carbs_feasibility: float = 100.0
    fat_feasibility: float = 100.0
    # 是否有警告
    has_warning: bool = False
    warning_message: str = ""


class FeasibilityService:
    """可行性计算服务"""
    
    # 预算到最大可达值的缓存
    _cache: Dict[int, Dict[str, int]] = {}
    
    def __init__(self):
        data_path = Path(__file__).parent.parent / "data" / "recipes.json"
        with open(data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        self.recipes = data.get('recipes', [])
        
        # 按餐次分类
        self.breakfast = [r for r in self.recipes if 'breakfast' in r.get('meal_type', [])]
        self.lunch = [r for r in self.recipes if 'lunch' in r.get('meal_type', [])]
        self.dinner = [r for r in self.recipes if 'dinner' in r.get('meal_type', [])]
        
        # 预计算常用预算值
        self._precompute_common_budgets()
    
    def _precompute_common_budgets(self):
        """预计算常用预算值的最大可达营养"""
        for budget in range(20, 205, 5):  # 20, 25, 30, ..., 200
            self._cache[budget] = self._compute_max_achievable(float(budget))
    
    def _compute_max_achievable(self, budget: float, items_per_meal: int = 2) -> Dict[str, int]:
        """
        贪心算法计算给定预算下的最大可达营养值
        
        策略: 对每餐次，优先选择热量/价格比最高的菜品
        """
        remaining = budget
        totals = {'calories': 0, 'protein': 0, 'carbs': 0, 'fat': 0}
        
        # 按热量/价格比排序每个餐次的菜品
        bf_sorted = sorted(self.breakfast, key=lambda x: x['calories'] / x['price'], reverse=True)
        lu_sorted = sorted(self.lunch, key=lambda x: x['calories'] / x['price'], reverse=True)
        dn_sorted = sorted(self.dinner, key=lambda x: x['calories'] / x['price'], reverse=True)
        
        for meal_list in [bf_sorted, lu_sorted, dn_sorted]:
            selected = 0
            for dish in meal_list:
                if selected >= items_per_meal:
                    break
                if dish['price'] <= remaining:
                    totals['calories'] += dish['calories']
                    totals['protein'] += dish['protein']
                    totals['carbs'] += dish['carbs']
                    totals['fat'] += dish['fat']
                    remaining -= dish['price']
                    selected += 1
        
        return {k: int(v) for k, v in totals.items()}
    
    def get_max_achievable(self, budget: float) -> Dict[str, int]:
        """获取给定预算下的最大可达营养值"""
        # 四舍五入到最近的5元
        budget_key = int(round(budget / 5) * 5)
        budget_key = max(20, min(budget_key, 200))
        
        if budget_key in self._cache:
            return self._cache[budget_key]
        
        return self._compute_max_achievable(budget)
    
    def check_feasibility(
        self,
        budget: float,
        target_calories: int,
        target_protein: int,
        target_carbs: int,
        target_fat: int,
        warning_threshold: float = 1.2,  # 超出20%开始警告
        error_threshold: float = 2.0     # 超出100%返回错误级别
    ) -> FeasibilityResult:
        """
        检查目标参数的可行性
        
        Returns:
            FeasibilityResult 包含可达性百分比和警告信息
        """
        max_vals = self.get_max_achievable(budget)
        
        # 计算各指标可达性(目标能达成的百分比)
        cal_feas = min(100.0, (max_vals['calories'] / target_calories * 100)) if target_calories > 0 else 100
        pro_feas = min(100.0, (max_vals['protein'] / target_protein * 100)) if target_protein > 0 else 100
        carb_feas = min(100.0, (max_vals['carbs'] / target_carbs * 100)) if target_carbs > 0 else 100
        fat_feas = min(100.0, (max_vals['fat'] / target_fat * 100)) if target_fat > 0 else 100
        
        # 判断是否需要警告
        has_warning = False
        warning_parts = []
        warning_type = "info"
        
        if cal_feas < 100:
            has_warning = True
            if cal_feas < (100 / error_threshold):  # < 50%
                warning_type = "error"
            elif cal_feas < (100 / warning_threshold):  # < 83%
                warning_type = "warning"
            warning_parts.append(f"热量最高可达{max_vals['calories']}kcal")
        
        if pro_feas < 100:
            has_warning = True
            warning_parts.append(f"蛋白质最高可达{max_vals['protein']}g")
        
        warning_message = ""
        if has_warning:
            warning_message = f"当前{budget:.0f}元预算下：" + "，".join(warning_parts)
        
        return FeasibilityResult(
            budget=budget,
            max_calories=max_vals['calories'],
            max_protein=max_vals['protein'],
            max_carbs=max_vals['carbs'],
            max_fat=max_vals['fat'],
            calories_feasibility=round(cal_feas, 1),
            protein_feasibility=round(pro_feas, 1),
            carbs_feasibility=round(carb_feas, 1),
            fat_feasibility=round(fat_feas, 1),
            has_warning=has_warning,
            warning_message=warning_message
        )


# 单例实例
feasibility_service = FeasibilityService()
