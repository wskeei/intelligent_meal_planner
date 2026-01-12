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
        
        # 定义观察空间 (状态空间) - 归一化后 [优化版: 13维]
        # [0] 当前步骤/max
        # [1] 累卡/目标, [2] 累蛋/目标, [3] 累碳/目标, [4] 累脂/目标
        # [5] 累花/预算
        # [6] 剩余卡/目标, [7] 剩余预算/预算
        # [8] 剩余步数/max (新增)
        # [9-11] 当前餐次one-hot: breakfast, lunch, dinner (新增)
        # [12] 多样性指标 (新增)
        # 范围设为 -2.0 ~ 2.0 (允许超出一倍，且剩余量可能是负数)
        self.observation_space = spaces.Box(
            low=-2.0,
            high=2.0,
            shape=(13,),
            dtype=np.float32
        )

        # 课程学习阶段 (用于训练时动态调整难度)
        self.curriculum_stage = 1  # 1=简单固定, 2=轻度随机, 3=完全随机
        self.global_step = 0  # 由外部trainer设置
        
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

        # ========== 课程学习 (Curriculum Learning) ==========
        # 根据训练进度动态调整难度
        if self.training_mode:
            # 根据global_step自动判断阶段
            if self.global_step < 100000:
                self.curriculum_stage = 1  # 简单固定
            elif self.global_step < 300000:
                self.curriculum_stage = 2  # 轻度随机
            else:
                self.curriculum_stage = 3  # 完全随机

            if self.curriculum_stage == 1:
                # ========== 阶段1: 简单固定目标 (0-100k steps) ==========
                # 让模型先学会基本的配餐逻辑
                self.target_calories = 2000.0
                self.budget_limit = 150.0  # 给足够宽松的预算
                self.target_protein = 100.0  # 20% 蛋白质
                self.target_carbs = 250.0    # 50% 碳水
                self.target_fat = 65.0       # 30% 脂肪

            elif self.curriculum_stage == 2:
                # ========== 阶段2: 轻度随机 (100k-300k steps) ==========
                # 在基础目标附近轻微波动
                self.target_calories = np.random.uniform(1800.0, 2200.0)
                self.budget_limit = np.random.uniform(120.0, 180.0)
                # 固定营养比例，减少变量
                self.target_protein = (self.target_calories * 0.20) / 4.0
                self.target_carbs = (self.target_calories * 0.50) / 4.0
                self.target_fat = (self.target_calories * 0.30) / 9.0

            else:
                # ========== 阶段3: 完全随机 (300k+ steps) ==========
                # 1. 随机化卡路里目标 (1200 ~ 3000 kcal) - 覆盖减脂到增肌
                self.target_calories = np.random.uniform(1200.0, 3000.0)

                # 2. 预算基于卡路里生成
                base_cost_per_100kcal = np.random.uniform(10.0, 16.0)
                estimated_cost = (self.target_calories / 100.0) * base_cost_per_100kcal
                self.budget_limit = np.clip(estimated_cost, 80.0, 400.0)

                # 3. 随机化营养比例
                mode_roll = np.random.random()

                if mode_roll < 0.2:
                    # Keto/低碳模式
                    carb_ratio = np.random.uniform(0.05, 0.15)
                    protein_ratio = np.random.uniform(0.20, 0.35)
                    fat_ratio = 1.0 - protein_ratio - carb_ratio
                elif mode_roll < 0.5:
                    # 健身/高蛋白模式
                    protein_ratio = np.random.uniform(0.30, 0.50)
                    fat_ratio = np.random.uniform(0.15, 0.25)
                    carb_ratio = 1.0 - protein_ratio - fat_ratio
                else:
                    # 均衡/普通模式
                    protein_ratio = np.random.uniform(0.15, 0.25)
                    fat_ratio = np.random.uniform(0.20, 0.35)
                    carb_ratio = 1.0 - protein_ratio - fat_ratio

                # 归一化
                total_ratio = protein_ratio + fat_ratio + carb_ratio
                protein_ratio /= total_ratio
                fat_ratio /= total_ratio
                carb_ratio /= total_ratio

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

        # 可行性检查：防止生成完全无解的低预算场景
        if self.training_mode:
            min_cost_6_items = 30.0  # 预估最小值 (5元/道 * 6)
            if self.budget_limit < min_cost_6_items * 1.2:
                self.budget_limit = min_cost_6_items * 1.2

        observation = self._get_observation()
        info = {
            'curriculum_stage': self.curriculum_stage if self.training_mode else 0,
            'target_calories': self.target_calories,
            'budget_limit': self.budget_limit
        }

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

        # [修复] 动作屏蔽应该已经阻止了错误餐次选择
        # 如果仍然发生，说明action_masks有bug，给极大惩罚并提前终止
        if current_meal_type not in recipe['meal_type']:
            print(f"[ERROR] Action masking failed! Selected {recipe['name']} for {current_meal_type}")
            return self._get_observation(), -100.0, True, False, {
                'error': 'Invalid meal type selection',
                'selected_recipe': recipe['name']
            }

        # 更新累计营养和花费
        self.total_calories += recipe['calories']
        self.total_protein += recipe['protein']
        self.total_carbs += recipe['carbs']
        self.total_fat += recipe['fat']
        self.total_cost += recipe['price']

        # 记录选择的菜品
        self.selected_recipes.append(recipe)
        self.selected_categories.append(recipe['category'])

        # 移动到下一步
        self.current_step_idx += 1

        # 检查是否完成一天的配餐
        terminated = self.current_step_idx >= self.max_steps
        truncated = False

        # ========== 奖励计算 ==========
        if terminated:
            # Episode结束时给予最终奖励
            reward = self._calculate_reward()
        else:
            # ========== 增强的中间步骤奖励 (Dense Reward) ==========
            reward = self._calculate_step_reward()

        observation = self._get_observation()
        info = {
            'selected_recipe': recipe['name'],
            'valid_action': True,
            'total_cost': self.total_cost,
            'total_calories': self.total_calories,
            'step': self.current_step_idx,
            'unique_categories': len(set(self.selected_categories))
        }

        return observation, reward, terminated, truncated, info

    def _calculate_step_reward(self) -> float:
        """
        计算中间步骤的即时奖励 (Dense Reward)
        目标：引导模型在每一步都朝着正确方向前进
        """
        reward = 0.0

        # 理想进度
        progress = self.current_step_idx / self.max_steps
        ideal_cal = progress * self.target_calories
        ideal_budget = progress * self.budget_limit

        # 1. 卡路里进度奖励 (范围: -2 到 +2)
        cal_deviation = abs(self.total_calories - ideal_cal)
        if cal_deviation < 100:
            cal_reward = 2.0 - (cal_deviation / 50.0)
        elif cal_deviation < 300:
            cal_reward = 1.0 - (cal_deviation - 100) / 200.0
        else:
            cal_reward = max(-2.0, 0.0 - (cal_deviation - 300) / 300.0)
        reward += cal_reward * 0.5  # 权重0.5

        # 2. 预算进度奖励 (范围: -1 到 +1)
        budget_deviation = self.total_cost - ideal_budget
        if budget_deviation <= 0:
            # 花费低于预期，轻微奖励
            budget_reward = 0.5
        elif budget_deviation < 10:
            # 花费略高，还可以接受
            budget_reward = 0.5 - (budget_deviation / 20.0)
        else:
            # 花费过高，惩罚
            budget_reward = max(-1.0, 0.0 - (budget_deviation / 30.0))
        reward += budget_reward * 0.3  # 权重0.3

        # 3. 多样性奖励 (鼓励选择不同类别的菜品)
        unique_categories = len(set(self.selected_categories))
        if unique_categories > 1:
            # 每多一个独特类别，奖励0.3分
            diversity_reward = (unique_categories - 1) * 0.3
            reward += diversity_reward

        # 4. 重复惩罚 (如果选了重复的菜品)
        recipe_names = [r['name'] for r in self.selected_recipes]
        if len(recipe_names) != len(set(recipe_names)):
            reward -= 1.0  # 选了重复的菜，扣分

        return reward
    
    def _get_observation(self) -> np.ndarray:
        """
        获取当前观察值 (归一化) - 13维版本
        """
        current_meal = self._get_current_meal_type()

        obs = np.array([
            # 原有的8维
            self.current_step_idx / self.max_steps,                              # [0] 当前进度
            self.total_calories / self.target_calories,                          # [1] 累计卡路里比例
            self.total_protein / self.target_protein,                            # [2] 累计蛋白质比例
            self.total_carbs / self.target_carbs,                                # [3] 累计碳水比例
            self.total_fat / self.target_fat,                                    # [4] 累计脂肪比例
            self.total_cost / self.budget_limit,                                 # [5] 累计花费比例
            (self.target_calories - self.total_calories) / self.target_calories, # [6] 剩余卡路里比例
            (self.budget_limit - self.total_cost) / self.budget_limit,           # [7] 剩余预算比例

            # 新增的5维
            (self.max_steps - self.current_step_idx) / self.max_steps,           # [8] 剩余步数比例
            float(current_meal == 'breakfast'),                                  # [9] 当前是否早餐
            float(current_meal == 'lunch'),                                      # [10] 当前是否午餐
            float(current_meal == 'dinner'),                                     # [11] 当前是否晚餐
            len(set(self.selected_categories)) / max(1, len(self.selected_recipes)),  # [12] 多样性指标
        ], dtype=np.float32)

        # 截断到 [-2.0, 2.0] 范围内，防止极值影响
        return np.clip(obs, -2.0, 2.0)
    
    def _nutrient_score(self, actual, target, max_bonus=10.0, tolerance=0.15):
        """
        简化版营养评分：线性分段奖励 (替代高斯函数)

        Args:
            actual: 实际值
            target: 目标值
            max_bonus: 最大奖励分数
            tolerance: 容忍度，例如0.15表示±15%内得满分

        Returns:
            score: 奖励分数
        """
        if target <= 0:
            return 0.0

        ratio = actual / target
        error = abs(ratio - 1.0)

        if error <= tolerance:
            # 在容忍范围内，给满分
            return max_bonus
        elif error <= tolerance * 2:
            # 在2倍容忍范围内，线性递减到50%
            return max_bonus * (1.0 - 0.5 * (error - tolerance) / tolerance)
        elif error <= tolerance * 3:
            # 在3倍容忍范围内，线性递减到0
            return max_bonus * 0.5 * (1.0 - (error - tolerance * 2) / tolerance)
        else:
            # 超出3倍容忍范围，给小幅惩罚
            return max(-max_bonus * 0.3, -error * max_bonus * 0.5)

    def _calculate_reward(self) -> float:
        """
        计算最终奖励 (Episode结束时)
        """
        # ========== 1. 营养达标奖励 ==========
        # 使用简化的线性分段奖励，不同营养素给予不同容忍度
        calorie_reward = self._nutrient_score(
            self.total_calories, self.target_calories,
            max_bonus=15.0, tolerance=0.10  # ±10% 卡路里得满分
        )
        protein_reward = self._nutrient_score(
            self.total_protein, self.target_protein,
            max_bonus=10.0, tolerance=0.20  # ±20% 蛋白质得满分
        )
        carbs_reward = self._nutrient_score(
            self.total_carbs, self.target_carbs,
            max_bonus=8.0, tolerance=0.25  # ±25% 碳水得满分
        )
        fat_reward = self._nutrient_score(
            self.total_fat, self.target_fat,
            max_bonus=7.0, tolerance=0.30  # ±30% 脂肪得满分 (最难控制)
        )

        # 总营养奖励 (最高40分)
        nutrition_reward = calorie_reward + protein_reward + carbs_reward + fat_reward

        # ========== 2. 预算奖励 ==========
        budget_ratio = self.total_cost / self.budget_limit
        if budget_ratio <= 0.90:
            # 花费低于90%，给予额外奖励
            budget_reward = 5.0
        elif budget_ratio <= 1.0:
            # 花费在90%-100%，正常奖励
            budget_reward = 3.0
        elif budget_ratio <= 1.05:
            # 花费在100%-105%，轻微惩罚
            budget_reward = 1.0
        elif budget_ratio <= 1.15:
            # 花费在105%-115%，中等惩罚
            budget_reward = -2.0
        else:
            # 超支超过15%，重惩罚
            budget_reward = max(-8.0, -5.0 - (budget_ratio - 1.15) * 20)

        # ========== 3. 多样性奖励 ==========
        unique_categories = len(set(self.selected_categories))
        unique_recipes = len(set(r['name'] for r in self.selected_recipes))

        if unique_categories >= 4:
            variety_reward = 6.0
        elif unique_categories >= 3:
            variety_reward = 4.0
        elif unique_categories >= 2:
            variety_reward = 2.0
        else:
            variety_reward = 0.0

        # 额外奖励：如果6道菜都不重复
        if unique_recipes == self.max_steps:
            variety_reward += 3.0

        # ========== 4. 忌口惩罚 ==========
        dislike_penalty = 0.0
        if self.disliked_tags:
            for recipe in self.selected_recipes:
                recipe_tags = set(recipe.get('tags', []))
                disliked = recipe_tags.intersection(set(self.disliked_tags))
                if disliked:
                    dislike_penalty -= 8.0  # 每触犯一个忌口扣8分

        # ========== 综合奖励 ==========
        total_reward = (
            self.weight_nutrition * nutrition_reward +
            self.weight_budget * budget_reward +
            self.weight_variety * variety_reward +
            dislike_penalty
        )

        # Debug输出 (训练时可见)
        cal_error = abs(self.total_calories - self.target_calories) / self.target_calories * 100
        print(f"[FINAL] R={total_reward:6.2f} | Nutri={nutrition_reward:5.1f} (CalErr:{cal_error:4.1f}%) | "
              f"Budg={budget_reward:4.1f} ({budget_ratio*100:.0f}%) | Var={variety_reward:3.1f} ({unique_categories}cat)")

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
        
        # 防死锁兜底逻辑优化
        if not possible_indices: 
            # 策略优化：如果没钱了，不能摆烂随便选（否则会选贵的导致罚分爆炸）
            # 我们强制模型只能选当前餐次中【价格最低】的菜，进行“止损”
            
            # 1. 找出所有属于当前餐次的菜品索引
            valid_meal_indices = [
                i for i, r in enumerate(self.recipes) 
                if current_meal_type in r['meal_type']
            ]
            
            if valid_meal_indices:
                # 2. 找到这些菜里的最低价格
                min_price = min(self.recipes[i]['price'] for i in valid_meal_indices)
                
                # 3. 只解锁价格等于最低价的菜
                for i in valid_meal_indices:
                    if self.recipes[i]['price'] == min_price:
                        mask[i] = True
            
            # 极少数情况：如果没有valid_meal_indices（说明数据库里没有这种餐次的菜），则全开防止报错
            if not np.any(mask):
                 mask[:] = True
                    
        return mask