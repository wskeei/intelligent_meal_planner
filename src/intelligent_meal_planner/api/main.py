"""
FastAPI 后端主应用

智能配餐系统 API 服务
"""

from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import time
import logging
import json
from pathlib import Path

from .routers import recipes_router, meal_plans_router, auth_router
from ..db import models, database
from sqlalchemy.orm import Session

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

def init_db():
    """Initialize DB and Migrate Data if empty"""
    models.Base.metadata.create_all(bind=database.engine)
    
    session = database.SessionLocal()
    try:
        # 1. Create Default User (root/123456)
        from .routers.auth import get_password_hash
        root_user = session.query(models.User).filter(models.User.username == "root").first()
        if not root_user:
            logger.info("Creating default user 'root'...")
            root_user = models.User(
                username="root",
                email="root@example.com",
                hashed_password=get_password_hash("123456"),
                age=30,
                gender="male",
                height=175,
                weight=70,
                activity_level="moderate",
                health_goal="healthy"
            )
            session.add(root_user)
            session.commit()

        # 2. Check if recipes exist
        if session.query(models.Recipe).count() == 0:
            logger.info("Migrating recipes from JSON to SQLite...")
            data_path = Path(__file__).parent.parent / "data" / "recipes.json"
            if data_path.exists():
                with open(data_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    recipes = data.get('recipes', [])
                    for r in recipes:
                        try:
                            new_recipe = models.Recipe(
                                id=r.get('id'),
                                name=r.get('name', 'Unknown'),
                                category=r.get('category', 'Uncategorized'),
                                calories=r.get('calories', 0),
                                protein=r.get('protein', 0),
                                carbs=r.get('carbs', 0),
                                fat=r.get('fat', 0),
                                price=r.get('price', 0),
                                cooking_time=r.get('cooking_time', 15),
                                description=r.get('description', ''),
                                tags=r.get('tags', []),
                                meal_type=r.get('meal_type', []),
                                ingredients=r.get('ingredients', ["Sample Ingredient 1", "Sample Ingredient 2"]),
                                instructions=r.get('instructions', ["Step 1: Prep", "Step 2: Cook"])
                            )
                            session.add(new_recipe)
                        except Exception as e:
                            logger.error(f"Skipping malformed recipe ID {r.get('id')}: {e}")
                    session.commit()
            logger.info("Migration complete.")
    finally:
        session.close()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info("🚀 智能配餐系统 API 启动中...")
    init_db()
    yield
    logger.info("👋 智能配餐系统 API 关闭")


app = FastAPI(
    title="智能配餐系统 API",
    description="Based on RL & Multi-Agent System",
    version="2.0.0",
    lifespan=lifespan
)

# CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
app.include_router(auth_router, prefix="/api")
app.include_router(recipes_router, prefix="/api")
app.include_router(meal_plans_router, prefix="/api")

@app.get("/", tags=["系统"])
async def root():
    return {"status": "running", "version": "2.0.0 (SQLite)"}

@app.get("/health", tags=["系统"])
async def health_check():
    return {"status": "healthy"}