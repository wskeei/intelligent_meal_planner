"""FastAPI application entrypoint."""

import json
import logging
import time
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from ..db import database, models
from .routers import (
    auth_router,
    meal_chat_router,
    meal_plans_router,
    recipes_router,
    shopping_lists_router,
    weekly_plans_router,
)

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init_db() -> None:
    """Initialize tables and seed the default user plus recipe catalog."""
    models.Base.metadata.create_all(bind=database.engine)

    session = database.SessionLocal()
    try:
        from .routers.auth import get_password_hash

        root_user = (
            session.query(models.User).filter(models.User.username == "root").first()
        )
        if not root_user:
            logger.info("Creating default user 'root'")
            root_user = models.User(
                username="root",
                email="root@example.com",
                hashed_password=get_password_hash("123456"),
                age=30,
                gender="male",
                height=175,
                weight=70,
                activity_level="moderate",
                health_goal="healthy",
            )
            session.add(root_user)
            session.commit()

        if session.query(models.Recipe).count() == 0:
            logger.info("Migrating recipes from JSON to SQLite")
            data_path = Path(__file__).parent.parent / "data" / "recipes.json"
            if data_path.exists():
                with open(data_path, "r", encoding="utf-8") as fh:
                    data = json.load(fh)
                for recipe in data.get("recipes", []):
                    try:
                        session.add(
                            models.Recipe(
                                id=recipe.get("id"),
                                name=recipe.get("name", "Unknown"),
                                category=recipe.get("category", "Uncategorized"),
                                calories=recipe.get("calories", 0),
                                protein=recipe.get("protein", 0),
                                carbs=recipe.get("carbs", 0),
                                fat=recipe.get("fat", 0),
                                price=recipe.get("price", 0),
                                cooking_time=recipe.get("cooking_time", 15),
                                description=recipe.get("description", ""),
                                tags=recipe.get("tags", []),
                                meal_type=recipe.get("meal_type", []),
                                ingredients=recipe.get("ingredients", []),
                                instructions=recipe.get("instructions", []),
                            )
                        )
                    except (
                        Exception
                    ) as exc:  # pragma: no cover - defensive logging only
                        logger.error(
                            "Skipping malformed recipe %s: %s", recipe.get("id"), exc
                        )
                session.commit()
    finally:
        session.close()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    logger.info("Starting API")
    init_db()
    yield
    logger.info("Stopping API")


app = FastAPI(
    title="Intelligent Meal Planner API",
    description="Conversational meal planning over RL and user profiles.",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    logger.info(
        "%s %s - %s - %.3fs",
        request.method,
        request.url.path,
        response.status_code,
        process_time,
    )
    return response


@app.exception_handler(Exception)
async def global_exception_handler(_request: Request, exc: Exception):
    logger.error("Unhandled exception: %s", exc)
    return JSONResponse(
        status_code=500,
        content={"success": False, "error": "服务器内部错误", "detail": str(exc)},
    )


app.include_router(auth_router, prefix="/api")
app.include_router(recipes_router, prefix="/api")
app.include_router(meal_chat_router, prefix="/api")
app.include_router(meal_plans_router, prefix="/api")
app.include_router(weekly_plans_router, prefix="/api")
app.include_router(shopping_lists_router, prefix="/api")


@app.get("/", tags=["system"])
async def root():
    return {"status": "running", "version": "2.0.0"}


@app.get("/health", tags=["system"])
async def health_check():
    return {"status": "healthy"}
