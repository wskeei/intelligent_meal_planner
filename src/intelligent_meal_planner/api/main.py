"""
FastAPI 后端主应用

提供配餐 API 接口
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List
import json

app = FastAPI(
    title="智能配餐系统 API",
    description="基于强化学习与多Agent协作的智能配餐系统",
    version="0.1.0"
)

# 配置 CORS（允许前端跨域访问）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 请求模型
class MealPlanRequest(BaseModel):
    """配餐请求参数"""
    user_request: Optional[str] = Field(None, description="用户的自然语言需求描述")
    target_calories: int = Field(default=2000, description="目标卡路里")
    target_protein: int = Field(default=100, description="目标蛋白质(g)")
    target_carbs: int = Field(default=250, description="目标碳水化合物(g)")
    target_fat: int = Field(default=60, description="目标脂肪(g)")
    max_budget: float = Field(default=50.0, description="最大预算(元)")
    use_agent: bool = Field(default=False, description="是否使用 Agent 对话模式")


class QuickPlanRequest(BaseModel):
    """快速配餐请求（直接调用 RL 模型）"""
    target_calories: int = Field(default=2000)
    target_protein: int = Field(default=100)
    target_carbs: int = Field(default=250)
    target_fat: int = Field(default=60)
    max_budget: float = Field(default=50.0)


# 响应模型
class MealPlanResponse(BaseModel):
    """配餐响应"""
    success: bool
    message: str
    data: Optional[dict] = None


@app.get("/")
async def root():
    """API 根路径"""
    return {
        "name": "智能配餐系统 API",
        "version": "0.1.0",
        "endpoints": {
            "/api/plan_meal": "POST - 生成配餐方案（Agent模式）",
            "/api/quick_plan": "POST - 快速生成配餐方案（直接RL模型）",
            "/api/recipes": "GET - 获取菜品列表",
            "/api/recipes/{id}": "GET - 获取菜品详情"
        }
    }


@app.post("/api/plan_meal", response_model=MealPlanResponse)
async def plan_meal(request: MealPlanRequest):
    """
    生成配餐方案
    
    如果 use_agent=True，使用 CrewAI Agent 进行对话式配餐
    否则直接调用 RL 模型生成方案
    """
    try:
        if request.use_agent and request.user_request:
            # Agent 模式
            from ..agents.crew import MealPlanningCrew
            crew = MealPlanningCrew()
            result = crew.plan_meal(request.user_request)
            return MealPlanResponse(success=True, message="配餐方案生成成功", data={"plan": result})
        else:
            # 直接 RL 模型模式
            from ..tools.rl_model_tool import create_rl_model_tool
            tool = create_rl_model_tool()
            result = tool._run(
                target_calories=request.target_calories,
                target_protein=request.target_protein,
                target_carbs=request.target_carbs,
                target_fat=request.target_fat,
                max_budget=request.max_budget
            )
            return MealPlanResponse(success=True, message="配餐方案生成成功", data=json.loads(result))
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=f"模型文件未找到: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成配餐方案失败: {str(e)}")


@app.post("/api/quick_plan", response_model=MealPlanResponse)
async def quick_plan(request: QuickPlanRequest):
    """快速生成配餐方案（直接调用 RL 模型）"""
    try:
        from ..tools.rl_model_tool import create_rl_model_tool
        tool = create_rl_model_tool()
        result = tool._run(
            target_calories=request.target_calories,
            target_protein=request.target_protein,
            target_carbs=request.target_carbs,
            target_fat=request.target_fat,
            max_budget=request.max_budget
        )
        return MealPlanResponse(success=True, message="配餐方案生成成功", data=json.loads(result))
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=f"模型文件未找到: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成配餐方案失败: {str(e)}")


@app.get("/api/recipes")
async def get_recipes(meal_type: Optional[str] = None, limit: int = 50):
    """获取菜品列表"""
    from ..tools.recipe_database_tool import recipe_db_tool
    result = recipe_db_tool._run(meal_type=meal_type, limit=limit)
    return {"success": True, "data": result}


@app.get("/api/recipes/{recipe_id}")
async def get_recipe(recipe_id: int):
    """获取单个菜品详情"""
    from ..tools.recipe_database_tool import recipe_db_tool
    result = recipe_db_tool._run(recipe_ids=[recipe_id])
    if "未找到" in result:
        raise HTTPException(status_code=404, detail="菜品不存在")
    return {"success": True, "data": result}


# 启动命令：uv run uvicorn intelligent_meal_planner.api.main:app --reload