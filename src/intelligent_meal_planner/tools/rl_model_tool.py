"""
强化学习模型工具 - 用于生成智能配餐方案

这个工具封装了训练好的 MaskablePPO 模型，提供以下功能：
1. 根据用户需求生成配餐方案
2. 支持自定义营养目标和预算
3. 支持忌口和偏好设置
4. 返回最优的菜品ID组合
"""

import json
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from sb3_contrib import MaskablePPO

# 导入我们的强化学习环境
import sys
sys.path.append(str(Path(__file__).parent.parent))
from rl.environment import MealPlanningEnv


class RLModelTool:
    """
    强化学习配餐模型工具
    
    功能：
    - 加载训练好的 MaskablePPO 模型
    - 根据用户需求生成最优配餐方案
    - 支持自定义营养目标、预算、忌口等
    """
    
    def __init__(self, model_path: Optional[str] = None):
        """
        初始化工具，加载 MaskablePPO 模型
        
        参数：
            model_path: 模型文件路径，如果为None则使用默认路径
        """
        self.name = "强化学习配餐模型"
        self.description = (
            "使用训练好的 MaskablePPO 模型生成最优配餐方案。"
            "输入用户的营养目标、预算限制、忌口食材等信息，"
            "返回最适合的一日三餐菜品ID组合。"
        )
        
        # 如果没有指定路径，使用项目根目录下的模型
        if model_path is None:
            project_root = Path(__file__).parent.parent.parent.parent
            model_path = project_root / "models" / "best_model.zip"
        
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
            print("[加载中] 正在加载 MaskablePPO 模型...")
            try:
                self.model = MaskablePPO.load(self.model_path)
                print("[OK] 模型加载成功")
            except Exception as e:
                print(f"[错误] 模型加载失败: {e}")
                raise
    
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
        # 注意: MaskablePPO 训练时使用了 ActionMasker 包装器
        # 在推理时，我们需要确保环境逻辑与训练时一致，特别是 action_masks 方法
        self.env = MealPlanningEnv(
            target_calories=target_calories,
            target_protein=target_protein,
            target_carbs=target_carbs,
            target_fat=target_fat,
            budget_limit=max_budget,
            disliked_tags=disliked_ingredients or [],
            training_mode=False # 推理模式
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
        使用 MaskablePPO 模型生成一日三餐配餐方案
        
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
        
        # 安全计数器防止死循环
        max_steps_safety = 20
        current_steps = 0
            
        while not done and current_steps < max_steps_safety:
            current_steps += 1
            
            # 确定当前是哪一餐 (环境每餐选2道菜，所以每2步是一餐)
            # 0,1 -> breakfast; 2,3 -> lunch; 4,5 -> dinner
            # 在返回字典中，我们只记录最后一个选择或者合并? 
            # 原始代码: meal_plan[meal_names[step_count]] = int(action)
            # 这里 step_count 只到 2 (0,1,2)，但环境有 6 步。
            # 我们需要调整逻辑以适配环境的 items_per_meal (2)
            
            # 使用 MaskablePPO 预测动作，必须传入 action_masks
            action_masks = self.env.action_masks()
            
            # deterministic=True 确保结果稳定
            action, _states = self.model.predict(obs, action_masks=action_masks, deterministic=True)
            
            # 执行动作
            obs, reward, terminated, truncated, info = self.env.step(action)
            done = terminated or truncated
            
            # 记录选择
            if info.get('valid_action', False):
                # 只有当完成了一餐的所有 items 时，我们才算这一餐“完成”了?
                # 或者我们将每餐的多个菜品ID都记录下来?
                # 为了简化前后端接口，目前 MealPlan 结构是一个餐次对应一个 Recipe ID (单品)
                # 但环境现在是每餐2个品。
                # 临时解决方案：只记录每餐的第一个或最后一个有效选择，或者修改返回结构。
                # 鉴于 frontend 似乎只显示一个品 ("recipe_id": ...), 我们暂时覆盖记录，
                # 或者最好是显示多品。但改前端动作太大。
                # 让我们看看 environment.py 的 step 逻辑:
                # current_step_idx += 1. 
                # meal_idx = self.current_step_idx // self.items_per_meal
                
                # 我们实际上每餐选了2个菜。
                # 让我们把每餐的菜品做成一个组合菜或者只展示其中一个主要的(比如卡路里高的)?
                # 或者，我们可以修改前端支持多菜品，但现在为了快速集成：
                # 我们只记录每餐的**最后一个**选择作为代表，或者我们 Hack 一下：
                # 让前端能显示 "Recipe A + Recipe B" ? 不行，它是 id 关联。
                
                # 决定：为了兼容旧前端，我们只取每餐的第一个选择作为 "主菜" 放入 map。
                # 实际计算营养时环境是累加了所有的。
                # 这样会导致前端显示的营养(单品)和总营养(多品)不一致。
                # ***这是一个必须解决的问题***
                
                # 修正方案：
                # 前端 MealItem 定义: recipe_id, recipe_name, ...
                # 如果我们不能改前端，那只能让 Backend 生成的 MealPlanResponse 里的 MealItem 包含聚合信息?
                # 或者，我们只让 Agent 跑 3 步? 
                # 不，模型是按 6 步训练的。
                
                # 让我们看 frontend 的 MealPlanView: v-for="meal in mealPlan.meals"
                # 它是一个列表。我们可以为同一餐次添加多个 MealItem !
                # 比如: { meal_type: 'breakfast', recipe_id: 101 }, { meal_type: 'breakfast', recipe_id: 102 }
                # 前端代码: <div class="meal-icon-side" :class="meal.meal_type">
                # 这样会显示两行早餐，这完全可以接受！
                
                recipe_name = info.get('selected_recipe', '未知')
                print(f"[配餐中] 步骤 {current_steps}: 选择 {recipe_name}")
                
                # 我们需要知道当前是属于哪一餐
                # 倒推 step: 刚执行完 step, current_step_idx 已经 +1
                # 之前的 index 是 self.env.current_step_idx - 1
                # meal_idx = (current_step_idx - 1) // 2
                
                # 由于无法直接访问 env 内部状态的 step_idx (除非修改 env 返回 info)
                # 我们可以自己维护 step count
                
                # 0, 1 -> Meal 0 (Breakfast)
                # 2, 3 -> Meal 1 (Lunch)
                # 4, 5 -> Meal 2 (Dinner)
                
                step_idx_zero_based = current_steps - 1
                meal_idx = step_idx_zero_based // 2
                
                if meal_idx < 3:
                    m_type = meal_names[meal_idx]
                    
                    # 记录到 meal_plan 中
                    # 为了支持多品，我们需要一个 way to 存储。
                    # 原来是 Dict[str, int]，key 是 meal_type。这不支持重复 key。
                    # 我们需要修改 _generate_meal_plan 的返回类型，或者 key naming hack.
                    
                    # Hack: 使用 'breakfast_1', 'breakfast_2' ...
                    # 并在 Service 层处理
                    key = f"{m_type}_{step_idx_zero_based % 2}" 
                    meal_plan[key] = int(action)

        
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
        """
        plans = []
        for i in range(num_plans):
            result_str = self._run(**kwargs)
            result = json.loads(result_str)
            plans.append(result)
        return plans


# 创建工具实例（供外部导入使用）
def create_rl_model_tool(model_path: Optional[str] = None) -> RLModelTool:
    return RLModelTool(model_path=model_path)