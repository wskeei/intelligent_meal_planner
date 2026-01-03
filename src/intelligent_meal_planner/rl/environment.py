"""
强化学习配餐环境
实现符合 Gymnasium 标准的配餐环境，用于训练 DQN 模型
"""

import json
import numpy as np
import gymnasium as gym
from gymnasium import spaces
from pathlib import Path
from typing import Dict, List, Tuple, Optional


class MealPlanningEnv(gym.Env):
    """
    配餐环境类
    
    状态空间：(当前餐次, 已摄入卡路里, 已摄入蛋白质, 已摄入碳水, 已摄入脂肪, 已花费预算)
    动作空间：从菜品数据库中选择一道菜品（离散动作）
    奖励函数：在一天配餐结束后计算综合奖励
    """
    
    metadata = {'render_modes': ['human']}
    
    def __init__(
        self,
        recipes_path: Optional[str] = None,
        target_calories: float = 2000.0,
        target_protein: float = 100.0,
        target_carbs: float = 250.0,
        target_fat: float = 65.0,
        budget_limit: float = 120.0,
        disliked_tags: Optional[List[str]] = None,
        weight_nutrition: float = 1.0,
        weight_budget: float = 0.5,
        weight_variety: float = 0.3,
        training_mode: bool = True,
    ):
        """
        初始化配餐环境
        
        Args:
            recipes_path: 菜品数据库路径
            target_calories: 目标总卡路里
            target_protein: 目标蛋白质(g)
            target_carbs: 目标碳水化合物(g)
            target_fat: 目标脂肪(g)
            budget_limit: 预算限制(元)
            disliked_tags: 忌口标签列表
            weight_nutrition: 营养奖励权重
            weight_budget: 预算奖励权重
            weight_variety: 多样性奖励权重
            training_mode: 是否为训练模式 (开启域随机化)
        """
        super().__init__()
        
        self.training_mode = training_mode
        self.default_target_calories = target_calories
        self.default_budget_limit = budget_limit
        self.default_target_protein = target_protein
        self.default_target_carbs = target_carbs
        self.default_target_fat = target_fat
        
        # 加载菜品数据库
        if recipes_path is None:
            # 默认路径
            recipes_path = Path(__file__).parent.parent / "data" / "recipes.json"
        
        with open(recipes_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.recipes = data['recipes']
        
        # 用户目标参数
        self.target_calories = target_calories
        self.target_protein = target_protein
        self.target_carbs = target_carbs
        self.target_fat = target_fat
        self.budget_limit = budget_limit
        self.disliked_tags = disliked_tags if disliked_tags else []
        
        # 奖励权重
        self.weight_nutrition = weight_nutrition
        self.weight_budget = weight_budget
        self.weight_variety = weight_variety
        
        # 餐次定义
        self.meal_types = ['breakfast', 'lunch', 'dinner']
        self.num_meals_per_day = len(self.meal_types)
        self.items_per_meal = 2 # 增加每餐菜品数量，提高解空间自由度 (3餐 x 2道 = 6道菜/天)
        self.max_steps = self.num_meals_per_day * self.items_per_meal
        
        # 定义观察空间 (状态空间) - 归一化后
        # [当前步骤/max, 累卡/目标, 累蛋/目标, 累碳/目标, 累脂/目标, 累花/预算]
        # 范围设为 0 ~ 2.0 (允许超出一倍)
        self.observation_space = spaces.Box(
            low=0.0,
            high=2.0,
            shape=(6,),
            dtype=np.float32
        )
        
        # 定义动作空间 (菜品选择)
        self.action_space = spaces.Discrete(len(self.recipes))
        
        # 初始化状态
        self.current_step_idx = 0
        self.total_calories = 0.0
        self.total_protein = 0.0
        self.total_carbs = 0.0
        self.total_fat = 0.0
        self.total_cost = 0.0
        self.selected_recipes = []
        self.selected_categories = []
    
    def reset(self, seed=None, options=None):
        """
        重置环境到初始状态
        
        Returns:
            observation: 初始观察值
            info: 额外信息字典
        """
        super().reset(seed=seed)
        

        # 域随机化 (仅在训练模式下)
        if self.training_mode:
            # 1. 随机化卡路里目标 (1200 ~ 3000 kcal) - 覆盖减脂到增肌
            self.target_calories = np.random.uniform(1200.0, 3000.0)
            
            # 2. 修改：预算应基于卡路里生成，并给予一定的浮动
            # 数据分析显示：Min Price/100kcal: 1.71, Median: 5.82
            # 我们设定一个合理的范围，比如 3.0 ~ 8.0 元/100kcal，保证大部分时候有解，偶尔紧巴巴
            base_cost_per_100kcal = np.random.uniform(3.0, 8.0) 
            estimated_cost = (self.target_calories / 100.0) * base_cost_per_100kcal
            
            # 设置预算，确保至少有 40 元保底，最高不超过 300
            self.budget_limit = np.clip(estimated_cost, 40.0, 300.0)
            
            # 3. 随机化营养比例 (Macros Distributions)
            # 为了让模型适应不同的饮食风格 (如低碳、高蛋白、均衡等)，我们随机生成宏量营养素比例
            
            # 随机生成三种饮食模式之一的概率
            mode_roll = np.random.random()
            
            if mode_roll < 0.2: 
                # Keto/低碳模式 (低碳水, 高脂肪)
                carb_ratio = np.random.uniform(0.05, 0.15)
                protein_ratio = np.random.uniform(0.20, 0.35)
                # 剩余给脂肪
                fat_ratio = 1.0 - protein_ratio - carb_ratio
            elif mode_roll < 0.5:
                # 健身/高蛋白模式 (高蛋白, 中碳水, 低脂)
                protein_ratio = np.random.uniform(0.30, 0.50)
                fat_ratio = np.random.uniform(0.15, 0.25)
                carb_ratio = 1.0 - protein_ratio - fat_ratio
            else:
                # 均衡/普通模式
                protein_ratio = np.random.uniform(0.15, 0.25)
                fat_ratio = np.random.uniform(0.20, 0.35)
                carb_ratio = 1.0 - protein_ratio - fat_ratio
                
            # 保证比例归一化 (防止浮点误差)
            total_ratio = protein_ratio + fat_ratio + carb_ratio
            if abs(mode_roll - 0.2) < 0.001: # Check if we were in keto logic (re-derive fat) -> simplified above, just normalize
                 pass
            
            # Calculate macros based on ratios and calories
            # 1g Protein = 4 kcal, 1g Carbs = 4 kcal, 1g Fat = 9 kcal
            
            # Re-normalize just in case
            protein_ratio = protein_ratio / total_ratio
            fat_ratio = fat_ratio / total_ratio
            carb_ratio = carb_ratio / total_ratio

            self.target_protein = (self.target_calories * protein_ratio) / 4.0
            self.target_carbs = (self.target_calories * carb_ratio) / 4.0
            self.target_fat = (self.target_calories * fat_ratio) / 9.0
            
        else:
            # 测试模式恢复默认
            self.target_calories = self.default_target_calories
            self.budget_limit = self.default_budget_limit
            self.target_protein = self.default_target_protein
            self.target_carbs = self.default_target_carbs
            self.target_fat = self.default_target_fat

        
        # 重置所有状态变量
        self.current_step_idx = 0
        self.total_calories = 0.0
        self.total_protein = 0.0
        self.total_carbs = 0.0
        self.total_fat = 0.0
        self.total_cost = 0.0
        self.selected_recipes = []
        self.selected_categories = []
        
        observation = self._get_observation()
        info = {}
        
        return observation, info
    
    def _get_current_meal_type(self):
        meal_idx = self.current_step_idx // self.items_per_meal
        if meal_idx >= len(self.meal_types):
            return "completed"
        return self.meal_types[meal_idx]

    def step(self, action: int) -> Tuple[np.ndarray, float, bool, bool, Dict]:
        """
        执行一个动作
        
        Args:
            action: 动作索引（菜品ID对应的索引）
        
        Returns:
            observation: 新的观察值
            reward: 奖励值
            terminated: 是否结束（完成三餐）
            truncated: 是否被截断
            info: 额外信息
        """
        # 获取选中的菜品
        recipe = self.recipes[action]
        
        # 检查菜品是否适合当前餐次
        current_meal_type = self._get_current_meal_type()
        
        # 如果菜品不适合当前餐次，给予惩罚
        if current_meal_type not in recipe['meal_type']:
            reward = -20.0  # 给予一次性惩罚
            # terminated = False # 不结束，允许重试，但RL通常是一步一动。为简化训练，我们仍继续。
            # Better strategy: Allow move but give huge penalty so it learns not to do it.
            # But if we terminate, it might be stuck. Let's just Penalty + Continue.
        else:
            reward = 0.0 # Base reward

        # 更新累计营养和花费
        self.total_calories += recipe['calories']
        self.total_protein += recipe['protein']
        self.total_carbs += recipe['carbs']
        self.total_fat += recipe['fat']
        self.total_cost += recipe['price']
        
        # 记录选择的菜品
        self.selected_recipes.append(recipe)
        self.selected_categories.append(recipe['category'])
        
        # 移动到下一餐
        self.current_step_idx += 1
        
        # 检查是否完成一天的配餐
        terminated = self.current_step_idx >= self.max_steps
        truncated = False
        
        # 计算奖励
        if terminated:
            reward += self._calculate_reward()
        else:
            # 中间步骤给予平滑的进度奖励 (增强引导)
            reward += 1.0
        
        observation = self._get_observation()
        info = {
            'selected_recipe': recipe['name'],
            'valid_action': True,
            'total_cost': self.total_cost,
            'total_calories': self.total_calories
        }
        
        return observation, reward, terminated, truncated, info
    
    def _get_observation(self) -> np.ndarray:
        """
        获取当前观察值 (归一化)
        """
        obs = np.array([
            self.current_step_idx / self.max_steps,
            self.total_calories / self.target_calories,
            self.total_protein / self.target_protein,
            self.total_carbs / self.target_carbs,
            self.total_fat / self.target_fat,
            self.total_cost / self.budget_limit
        ], dtype=np.float32)
        
        # 截断到 [0, 2.0] 范围内，防止极值影响
        return np.clip(obs, 0.0, 2.0)
    
    def _calculate_reward(self) -> float:
        """
        计算最终奖励
        
        综合考虑：
        1. 营养达标程度 (优化版：放宽标准差，提供更平滑的梯度)
        2. 预算控制 (优化版：降低基础奖励，避免不想努力)
        3. 菜品多样性
        4. 忌口惩罚
        
        Returns:
            总奖励值
        """
        # 1. 营养达标奖励（使用高斯函数）
        nutrition_reward = 0.0
        
        # 卡路里偏差 (标准差 500 -> 800，老师建议)
        calorie_diff = abs(self.total_calories - self.target_calories)
        calorie_reward = np.exp(-calorie_diff / 800.0) * 10 
        
        # 蛋白质偏差 (标准差 50 -> 80，老师建议)
        protein_diff = abs(self.total_protein - self.target_protein)
        protein_reward = np.exp(-protein_diff / 80.0) * 10
        
        # 碳水偏差 (标准差 100 -> 150)
        carbs_diff = abs(self.total_carbs - self.target_carbs)
        carbs_reward = np.exp(-carbs_diff / 150.0) * 10
        
        # 脂肪偏差 (标准差 30 -> 50)
        fat_diff = abs(self.total_fat - self.target_fat)
        fat_reward = np.exp(-fat_diff / 50.0) * 10
        
        nutrition_reward = (calorie_reward + protein_reward + carbs_reward + fat_reward) / 4.0
        
        # 2. 预算奖励
        if self.total_cost <= self.budget_limit:
            budget_reward = 2.0  # 10.0 -> 2.0 (不再喧宾夺主，只要合格就行)
        else:
            # 超出预算给予惩罚
            over_budget = self.total_cost - self.budget_limit
            # 保持惩罚力度，或者稍微加大
            budget_reward = max(-20.0, -over_budget * 2.0) 
        
        # 3. 多样性奖励
        variety_reward = 0.0
        unique_categories = len(set(self.selected_categories))
        if unique_categories >= 3:
            variety_reward = 5.0
        if unique_categories >= 2: # 稍微给点鼓励
            variety_reward += 2.0
        
        # 4. 忌口惩罚
        dislike_penalty = 0.0
        for recipe in self.selected_recipes:
            recipe_tags = set(recipe['tags'])
            if self.disliked_tags:
                disliked = recipe_tags.intersection(set(self.disliked_tags))
                if disliked:
                    dislike_penalty -= 50.0  # 严重惩罚
        
        # 综合奖励
        total_reward = (
            self.weight_nutrition * nutrition_reward +
            self.weight_budget * budget_reward +
            self.weight_variety * variety_reward +
            dislike_penalty
        )
        
        # Debug Print (Visible in console during training)
        # This helps us see WHY the score is low (e.g. is it Nutrition or Budget?)
        print(f"[DEBUG] Score={total_reward:5.2f} | Nutri={nutrition_reward:5.2f} (CalDiff:{calorie_diff:4.0f}) | Budg={budget_reward:5.1f} | Var={variety_reward:3.1f}")
        
        return total_reward
    
    def render(self):
        """
        渲染环境状态（用于调试）
        """
        print(f"\n{'='*60}")
        print(f"当前进度: {self.current_step_idx}/{self.max_steps}")
        print(f"累计营养: 卡路里={self.total_calories:.1f}, 蛋白质={self.total_protein:.1f}g, "
              f"碳水={self.total_carbs:.1f}g, 脂肪={self.total_fat:.1f}g")
        print(f"累计花费: {self.total_cost:.1f}元")
        print(f"\n已选菜品:")
        for i, recipe in enumerate(self.selected_recipes):
            print(f"  {i+1}. {recipe['name']} ({recipe['category']}) - {recipe['calories']}卡 - {recipe['price']}元")
        print(f"{'='*60}\n")
    
    def get_valid_actions(self) -> List[int]:
        """
        获取当前状态下的有效动作（适合当前餐次的菜品）
        保留此方法用于兼容性
        """
        if self.current_step_idx >= self.max_steps:
            return []
        
        current_meal_type = self._get_current_meal_type()
        valid_actions = []
        
        for i, recipe in enumerate(self.recipes):
            if current_meal_type in recipe['meal_type']:
                valid_actions.append(i)
        
        return valid_actions

    def action_masks(self) -> np.ndarray:
        """
        生成动作掩码：屏蔽无效动作。
        1. 必须符合当前餐次 (早餐只能选早餐菜)
        2. [新增] 必须买得起 (当前价格 <= 剩余预算 + 缓冲)
        """
        mask = np.zeros(self.action_space.n, dtype=bool)
        
        if self.current_step_idx >= self.max_steps:
            return mask 
            
        current_meal_type = self._get_current_meal_type()
        
        # 计算剩余预算，并给予一定的浮动 (例如允许超支 10% 用于最后微调)
        remaining_budget = self.budget_limit - self.total_cost
        budget_buffer = self.budget_limit * 0.10 
        max_affordable_price = remaining_budget + budget_buffer
        
        possible_indices = []
        
        for i, recipe in enumerate(self.recipes):
            # 只有同时满足：1. 餐次对，2. 价格别太离谱，才允许选
            if current_meal_type in recipe['meal_type']:
                if recipe['price'] <= max_affordable_price:
                    mask[i] = True
                    possible_indices.append(i)
                else:
                    # 如果太贵了，直接屏蔽，不让模型选
                    mask[i] = False
        
        # 防死锁兜底：如果这一餐所有符合餐次的菜都买不起（mask全false），
        # 则放开价格限制，允许它选符合餐次的任意菜（哪怕被罚分也要走完这一步，不能卡死程序）
        if not possible_indices: 
            for i, recipe in enumerate(self.recipes):
                if current_meal_type in recipe['meal_type']:
                    mask[i] = True
                    
        return mask