"""
强化学习模型工具 - 用于生成智能配餐方案

这个工具封装了训练好的 DQN 模型，提供以下功能：
1. 根据用户需求生成配餐方案
2. 支持自定义营养目标和预算
3. 支持忌口和偏好设置
4. 返回最优的菜品ID组合
"""

import json
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from stable_baselines3 import DQN

# 导入我们的强化学习环境
import sys
sys.path.append(str(Path(__file__).parent.parent))
from rl.environment import MealPlanningEnv


class RLModelTool:
    """
    强化学习配餐模型工具
    
    功能：
    - 加载训练好的 DQN 模型
    - 根据用户需求生成最优配餐方案
    - 支持自定义营养目标、预算、忌口等
    """
    
    def __init__(self, model_path: Optional[str] = None):
        """
        初始化工具，加载 DQN 模型
        
        参数：
            model_path: 模型文件路径，如果为None则使用默认路径
        """
        self.name = "强化学习配餐模型"
        self.description = (
            "使用训练好的深度Q网络(DQN)模型生成最优配餐方案。"
            "输入用户的营养目标、预算限制、忌口食材等信息，"
            "返回最适合的一日三餐菜品ID组合。"
        )
        
        # 如果没有指定路径，使用项目根目录下的模型
        if model_path is None:
            project_root = Path(__file__).parent.parent.parent.parent
            model_path = project_root / "models" / "checkpoints" / "dqn_meal_planner_10000_steps.zip"
        
        self.model_path = Path(model_path)
        
        # 检查模型文件是否存在
        if not self.model_path.exists():
            raise FileNotFoundError(f"模型文件不存在: {self.model_path}")
        
        # 加载模型（延迟加载，第一次使用时才加载）
        self.model = None
        self.env = None
        
        print(f"[OK] 强化学习模型工具已初始化")
        print(f"     模型路径: {self.model_path}")
    
    def _load_model(self):
        """延迟加载模型（第一次调用时执行）"""
        if self.model is None:
            print("[加载中] 正在加载 DQN 模型...")
            self.model = DQN.load(self.model_path)
            print("[OK] 模型加载成功")
    
    def _run(self,
             target_calories: int = 2000,
             target_protein: int = 100,
             target_carbs: int = 250,
             target_fat: int = 60,
             max_budget: float = 50.0,
             disliked_ingredients: Optional[List[str]] = None,
             preferred_tags: Optional[List[str]] = None) -> str:
        """
        生成配餐方案
        
        参数：
            target_calories: 目标卡路里 (kcal)
            target_protein: 目标蛋白质 (g)
            target_carbs: 目标碳水化合物 (g)
            target_fat: 目标脂肪 (g)
            max_budget: 最大预算 (元)
            disliked_ingredients: 忌口食材列表
            preferred_tags: 偏好标签列表
            
        返回：
            包含推荐菜品ID的JSON字符串
        """
        
        # 延迟加载模型
        self._load_model()
        
        # 创建环境（使用用户的目标值）
        self.env = MealPlanningEnv(
            target_calories=target_calories,
            target_protein=target_protein,
            target_carbs=target_carbs,
            target_fat=target_fat,
            budget_limit=max_budget,
            disliked_tags=disliked_ingredients or []
        )
        
        # 使用模型生成配餐方案
        meal_plan, metrics = self._generate_meal_plan()
        
        # 格式化输出
        result = {
            'meal_plan': meal_plan,
            'metrics': metrics,
            'target': {
                'calories': target_calories,
                'protein': target_protein,
                'carbs': target_carbs,
                'fat': target_fat,
                'budget': max_budget
            }
        }
        
        return json.dumps(result, ensure_ascii=False, indent=2)
    
    def _generate_meal_plan(self) -> Tuple[Dict[str, int], Dict[str, Any]]:
        """
        使用 DQN 模型生成一日三餐配餐方案
        
        返回：
            (meal_plan, metrics) 元组
            - meal_plan: {'breakfast': recipe_id, 'lunch': recipe_id, 'dinner': recipe_id}
            - metrics: 包含营养达成情况和总花费的字典
        """
        
        print("\n[配餐中] 开始生成配餐方案...")
        
        # 重置环境
        obs, info = self.env.reset()
        
        meal_plan = {}
        meal_names = ['breakfast', 'lunch', 'dinner']
        
        done = False
        step_count = 0
        while not done:
            print(f"[配餐中] 正在为 {meal_names[step_count]} 选择菜品...")
            
            # 使用模型预测动作
            action, _states = self.model.predict(obs, deterministic=True)
            
            # 执行动作
            obs, reward, terminated, truncated, info = self.env.step(action)
            done = terminated or truncated
            
            # 记录当前餐次的选择
            if info.get('valid_action', False):
                meal_plan[meal_names[step_count]] = int(action)
                print(f"[配餐中] {meal_names[step_count]} 选择完成: {info.get('selected_recipe', '未知')}")
                step_count += 1
        
        print("[配餐中] 配餐方案生成完成！\n")
        
        # 计算最终指标
        metrics = {
            'total_calories': self.env.total_calories,
            'total_protein': self.env.total_protein,
            'total_carbs': self.env.total_carbs,
            'total_fat': self.env.total_fat,
            'total_cost': self.env.total_cost,
            'final_reward': reward,
            'calories_achievement': (self.env.total_calories / self.env.target_calories) * 100,
            'protein_achievement': (self.env.total_protein / self.env.target_protein) * 100,
            'budget_usage': (self.env.total_cost / self.env.budget_limit) * 100
        }
        
        return meal_plan, metrics
    
    def generate_multiple_plans(self, 
                                num_plans: int = 3,
                                **kwargs) -> List[Dict[str, Any]]:
        """
        生成多个配餐方案供用户选择
        
        参数：
            num_plans: 生成方案的数量
            **kwargs: 传递给 _run 的参数
            
        返回：
            配餐方案列表
        """
        plans = []
        
        for i in range(num_plans):
            # 添加一些随机性来生成不同的方案
            result_str = self._run(**kwargs)
            result = json.loads(result_str)
            plans.append(result)
        
        return plans


# 创建工具实例（供外部导入使用）
def create_rl_model_tool(model_path: Optional[str] = None) -> RLModelTool:
    """
    创建 RL 模型工具实例的工厂函数
    
    参数：
        model_path: 模型文件路径
        
    返回：
        RLModelTool 实例
    """
    return RLModelTool(model_path=model_path)