"""
配餐团队 Crew

协调 UserProfilerAgent 和 RLChefAgent 完成配餐任务
"""

from crewai import Crew, Task, Process
from typing import Optional, Dict, Any
from .user_profiler import UserProfilerAgent
from .rl_chef import RLChefAgent


class MealPlanningCrew:
    """智能配餐团队 - 协调多个 Agent 完成配餐任务"""
    
    def __init__(self, llm=None):
        """
        初始化配餐团队
        
        Args:
            llm: 语言模型实例（可选，默认使用 DeepSeek 或 CrewAI 配置的模型）
        """
        if llm is None:
            import os
            from langchain_openai import ChatOpenAI
            
            api_key = os.getenv("DEEPSEEK_API_KEY")
            api_base = os.getenv("DEEPSEEK_API_BASE", "https://api.deepseek.com/v1")
            model = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
            
            if api_key:
                llm = ChatOpenAI(
                    model=model,
                    base_url=api_base,
                    api_key=api_key,
                    temperature=0.7
                )
        
        self.llm = llm
        self.profiler = UserProfilerAgent.create(llm)
        self.chef = RLChefAgent.create(llm)
    
    def plan_meal(self, user_request: str) -> str:
        """
        根据用户请求生成配餐方案
        
        Args:
            user_request: 用户的配餐需求描述
        
        Returns:
            配餐方案文本
        """
        # 定义任务1：分析用户需求
        analyze_task = Task(
            description=f"""分析用户的配餐需求，提取关键信息。

用户输入：{user_request}

请提取以下信息并以 JSON 格式输出：
1. target_calories: 目标卡路里（默认2000）
2. target_protein: 目标蛋白质克数（默认100）
3. target_carbs: 目标碳水克数（默认250）
4. target_fat: 目标脂肪克数（默认60）
5. max_budget: 最大预算元（默认50）
6. health_goal: 健康目标（如减脂、增肌、维持）
7. disliked_foods: 忌口食物列表
8. preferences: 口味偏好

输出格式示例：
```json
{{
    "target_calories": 1800,
    "target_protein": 120,
    "target_carbs": 200,
    "target_fat": 50,
    "max_budget": 40,
    "health_goal": "减脂",
    "disliked_foods": ["辣椒", "香菜"],
    "preferences": ["清淡", "少油"]
}}
```""",
            expected_output="JSON 格式的用户需求报告",
            agent=self.profiler
        )
        
        # 定义任务2：生成配餐方案
        plan_task = Task(
            description="""根据用户需求分析结果，使用 RL 模型生成配餐方案。

步骤：
1. 从上一个任务获取用户的营养目标和预算
2. 调用 meal_plan_generator 工具生成配餐方案
3. 调用 recipe_query 工具获取推荐菜品的详细信息
4. 整理成易读的配餐报告

输出应包含：
- 早餐、午餐、晚餐的具体菜品
- 每道菜的营养信息和价格
- 全天营养汇总
- 总花费
- 营养目标达成情况""",
            expected_output="完整的一日三餐配餐方案",
            agent=self.chef,
            context=[analyze_task]
        )
        
        # 创建团队并执行
        crew = Crew(
            agents=[self.profiler, self.chef],
            tasks=[analyze_task, plan_task],
            process=Process.sequential,
            verbose=True
        )
        
        result = crew.kickoff()
        return str(result)
    
    def quick_plan(self, 
                   target_calories: int = 2000,
                   target_protein: int = 100,
                   target_carbs: int = 250,
                   target_fat: int = 60,
                   max_budget: float = 50.0) -> str:
        """
        快速生成配餐方案（跳过对话分析，直接使用参数）
        
        Args:
            target_calories: 目标卡路里
            target_protein: 目标蛋白质
            target_carbs: 目标碳水
            target_fat: 目标脂肪
            max_budget: 最大预算
        
        Returns:
            配餐方案文本
        """
        plan_task = Task(
            description=f"""使用以下参数生成配餐方案：
- 目标卡路里: {target_calories} kcal
- 目标蛋白质: {target_protein} g
- 目标碳水: {target_carbs} g
- 目标脂肪: {target_fat} g
- 预算上限: {max_budget} 元

步骤：
1. 调用 meal_plan_generator 工具，传入上述参数
2. 调用 recipe_query 工具获取推荐菜品详情
3. 生成配餐报告""",
            expected_output="完整的一日三餐配餐方案",
            agent=self.chef
        )
        
        crew = Crew(
            agents=[self.chef],
            tasks=[plan_task],
            process=Process.sequential,
            verbose=True
        )
        
        result = crew.kickoff()
        return str(result)