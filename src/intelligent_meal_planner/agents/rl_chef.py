"""
强化学习配餐师 Agent

负责根据用户需求调用 RL 模型生成配餐方案，并查询菜品详情
"""

from crewai import Agent
from crewai.tools import BaseTool
from typing import Optional, Type
from pydantic import BaseModel, Field


class MealPlanInput(BaseModel):
    """配餐工具的输入参数"""
    target_calories: int = Field(default=2000, description="目标卡路里")
    target_protein: int = Field(default=100, description="目标蛋白质(g)")
    target_carbs: int = Field(default=250, description="目标碳水化合物(g)")
    target_fat: int = Field(default=60, description="目标脂肪(g)")
    max_budget: float = Field(default=50.0, description="最大预算(元)")


class RecipeQueryInput(BaseModel):
    """菜品查询工具的输入参数"""
    recipe_ids: str = Field(description="菜品ID列表，用逗号分隔，如 '1,5,10'")


class MealPlanTool(BaseTool):
    """调用 RL 模型生成配餐方案的工具"""
    name: str = "meal_plan_generator"
    description: str = "使用强化学习模型生成最优配餐方案。输入营养目标和预算，返回推荐的菜品ID。"
    args_schema: Type[BaseModel] = MealPlanInput
    
    def _run(self, target_calories: int = 2000, target_protein: int = 100,
             target_carbs: int = 250, target_fat: int = 60, max_budget: float = 50.0) -> str:
        from ..tools.rl_model_tool import create_rl_model_tool
        try:
            tool = create_rl_model_tool()
            return tool._run(
                target_calories=target_calories,
                target_protein=target_protein,
                target_carbs=target_carbs,
                target_fat=target_fat,
                max_budget=max_budget
            )
        except FileNotFoundError:
            return '{"error": "CRITICAL: Agent Loop Prevention. The RL model file is missing. Do NOT retry this tool. Please inform the user that the model needs to be trained first using the training script."}'


class RecipeQueryTool(BaseTool):
    """查询菜品详情的工具"""
    name: str = "recipe_query"
    description: str = "根据菜品ID查询详细信息，包括名称、营养成分、价格等。"
    args_schema: Type[BaseModel] = RecipeQueryInput
    
    def _run(self, recipe_ids: str) -> str:
        from ..tools.recipe_database_tool import recipe_db_tool
        ids = [int(x.strip()) for x in recipe_ids.split(',')]
        return recipe_db_tool._run(recipe_ids=ids)


class RLChefAgent:
    """强化学习配餐师 - 使用 RL 模型生成配餐方案"""
    
    @staticmethod
    def create(llm=None) -> Agent:
        """
        创建强化学习配餐师 Agent
        
        Args:
            llm: 语言模型实例（可选）
        
        Returns:
            配置好的 Agent 实例
        """
        return Agent(
            role="强化学习配餐师",
            goal="根据用户需求，使用 AI 模型生成最优的一日三餐配餐方案",
            backstory="""你是一位精通人工智能的营养配餐专家。
你掌握了先进的强化学习技术，能够根据用户的营养目标、预算限制和口味偏好，
智能地从数百道菜品中选择最优组合。
你会调用 RL 模型获取推荐，然后查询菜品详情，最终生成图文并茂的配餐方案。""",
            tools=[MealPlanTool(), RecipeQueryTool()],
            verbose=True,
            allow_delegation=False,
            llm=llm
        )