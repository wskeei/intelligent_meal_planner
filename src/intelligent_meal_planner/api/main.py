"""
FastAPI 后端主应用

智能配餐系统 API 服务
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import time
import logging

from .routers import recipes_router, meal_plans_router

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info("🚀 智能配餐系统 API 启动中...")
    yield
    logger.info("👋 智能配餐系统 API 关闭")


app = FastAPI(
    title="智能配餐系统 API",
    description="""
## 基于强化学习与多Agent协作的智能配餐系统

### 功能特性
- 🤖 **强化学习配餐**: 使用 DQN 算法优化营养搭配
- 🎯 **个性化推荐**: 支持自定义营养目标和预算
- 💬 **智能对话**: 可选 Agent 对话模式
- 📊 **营养分析**: 详细的营养达成情况分析

### 技术栈
- FastAPI + Pydantic
- Stable-Baselines3 (DQN)
- CrewAI (多Agent)
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 请求日志中间件
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    logger.info(f"{request.method} {request.url.path} - {response.status_code} - {process_time:.3f}s")
    return response


# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"未处理的异常: {exc}")
    return JSONResponse(
        status_code=500,
        content={"success": False, "error": "服务器内部错误", "detail": str(exc)}
    )


# 注册路由
app.include_router(recipes_router, prefix="/api")
app.include_router(meal_plans_router, prefix="/api")


@app.get("/", tags=["系统"])
async def root():
    """API 根路径 - 系统信息"""
    return {
        "name": "智能配餐系统 API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "endpoints": {
            "recipes": "/api/recipes",
            "meal_plans": "/api/meal-plans"
        }
    }


@app.get("/health", tags=["系统"])
async def health_check():
    """健康检查"""
    return {"status": "healthy"}


# 启动命令：
# uv run uvicorn intelligent_meal_planner.api.main:app --reload --host 0.0.0.0 --port 8000