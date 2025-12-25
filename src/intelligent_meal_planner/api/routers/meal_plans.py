"""
配餐方案相关 API 路由
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List

from ..schemas import (
    MealPlanRequest, MealPlanResponse, MealPlanHistory,
    UserPreferences, HealthGoal
)
from ..services import meal_plan_service

router = APIRouter(prefix="/meal-plans", tags=["配餐方案"])


@router.post("", response_model=MealPlanResponse, summary="生成配餐方案")
async def create_meal_plan(request: MealPlanRequest):
    """
    根据用户偏好生成智能配餐方案
    
    - 使用强化学习模型优化营养搭配
    - 支持自定义营养目标和预算
    - 可选使用 Agent 对话模式
    """
    preferences = request.preferences or UserPreferences()
    
    if request.use_agent and request.user_message:
        # Agent 模式（需要 LLM API Key）
        try:
            from ...agents.crew import MealPlanningCrew
            crew = MealPlanningCrew()
            crew_output = crew.plan_meal(request.user_message)
            
            # 使用 Agent 分析出的偏好覆盖默认偏好
            agent_prefs = crew_output.get("preferences", {})
            if agent_prefs:
                # 更新 preferences 对象
                # 注意：这里我们信任 Agent 提取的数值
                if "target_calories" in agent_prefs: preferences.target_calories = agent_prefs["target_calories"]
                if "target_protein" in agent_prefs: preferences.target_protein = agent_prefs["target_protein"]
                if "target_carbs" in agent_prefs: preferences.target_carbs = agent_prefs["target_carbs"]
                if "target_fat" in agent_prefs: preferences.target_fat = agent_prefs["target_fat"]
                if "max_budget" in agent_prefs: preferences.max_budget = agent_prefs["max_budget"]
                if "health_goal" in agent_prefs: preferences.health_goal = agent_prefs["health_goal"]
                if "disliked_foods" in agent_prefs: preferences.disliked_foods = agent_prefs["disliked_foods"]
                
                # 记录一下 Agent 的分析结果，方便调试
                print(f"DEBUG: Agent extracted preferences: {agent_prefs}")

            # 解析 Agent 返回结果... (这里其实我们主要用了 Agent 的分析结果来生成结构化数据)
            # 如果需要保留 Agent 的文本回复作为某种 message 返回给前端，目前 schema 不支持，
            # 但主要需求是生成正确的配餐，所以我们用更新后的 preferences 调用 generate_plan
            
            return meal_plan_service.generate_plan(preferences)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Agent 模式失败: {str(e)}")
    
    # 直接 RL 模型模式
    return meal_plan_service.generate_plan(preferences)


@router.post("/quick", response_model=MealPlanResponse, summary="快速配餐")
async def quick_plan(
    health_goal: HealthGoal = HealthGoal.HEALTHY,
    budget: float = 50.0
):
    """
    快速生成配餐方案（使用预设参数）
    
    根据健康目标自动设置营养参数：
    - lose_weight: 低卡路里、高蛋白
    - gain_muscle: 高卡路里、高蛋白
    - maintain: 均衡营养
    - healthy: 标准健康饮食
    """
    presets = {
        HealthGoal.LOSE_WEIGHT: UserPreferences(
            health_goal=health_goal,
            target_calories=1500,
            target_protein=120,
            target_carbs=150,
            target_fat=45,
            max_budget=budget
        ),
        HealthGoal.GAIN_MUSCLE: UserPreferences(
            health_goal=health_goal,
            target_calories=2500,
            target_protein=150,
            target_carbs=300,
            target_fat=80,
            max_budget=budget
        ),
        HealthGoal.MAINTAIN: UserPreferences(
            health_goal=health_goal,
            target_calories=2000,
            target_protein=100,
            target_carbs=250,
            target_fat=65,
            max_budget=budget
        ),
        HealthGoal.HEALTHY: UserPreferences(
            health_goal=health_goal,
            target_calories=1800,
            target_protein=90,
            target_carbs=220,
            target_fat=55,
            max_budget=budget
        )
    }
    
    preferences = presets.get(health_goal, presets[HealthGoal.HEALTHY])
    return meal_plan_service.generate_plan(preferences)


@router.get("", response_model=List[MealPlanResponse], summary="获取配餐历史")
async def get_history(limit: int = 10):
    """获取最近的配餐历史记录"""
    return meal_plan_service.get_history(limit)


@router.get("/{plan_id}", response_model=MealPlanResponse, summary="获取配餐详情")
async def get_plan(plan_id: str):
    """根据ID获取配餐方案详情"""
    plan = meal_plan_service.get_by_id(plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="配餐方案不存在")
    return plan