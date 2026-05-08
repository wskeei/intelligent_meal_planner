"""FastAPI application entrypoint."""

import json
import logging
import time
import uuid
from contextlib import asynccontextmanager
from contextvars import ContextVar
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pythonjsonlogger import jsonlogger

from ..db import database, models
from .routers import (
    auth_router,
    dashboard_router,
    intake_router,
    meal_chat_router,
    meal_plans_router,
    recipes_router,
    shopping_lists_router,
    weekly_plans_router,
)

load_dotenv()

# Context variable to store request ID across the request lifecycle
request_id_var: ContextVar[str] = ContextVar("request_id", default="")


class RequestIDFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter that includes request ID in all log records."""

    def add_fields(self, log_record: dict, record: logging.LogRecord, message_dict: dict):
        super().add_fields(log_record, record, message_dict)

        # Add request ID if available
        request_id = request_id_var.get()
        if request_id:
            log_record["request_id"] = request_id

        # Add standard fields
        log_record["level"] = record.levelname
        log_record["logger"] = record.name
        log_record["module"] = record.module
        log_record["function"] = record.funcName
        log_record["line"] = record.lineno


def setup_logging():
    """Configure structured JSON logging."""
    log_handler = logging.StreamHandler()
    formatter = RequestIDFormatter(
        "%(timestamp)s %(level)s %(name)s %(message)s",
        timestamp=True,
    )
    log_handler.setFormatter(formatter)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.handlers = [log_handler]

    return logging.getLogger(__name__)


logger = setup_logging()


def run_migrations() -> bool:
    """Run Alembic migrations. Returns True if successful."""
    try:
        from alembic.config import Config
        from alembic import command

        alembic_cfg = Config("alembic.ini")
        command.upgrade(alembic_cfg, "head")
        logger.info("Alembic migrations applied successfully")
        return True
    except Exception as e:
        logger.warning("Alembic migrations failed, falling back to create_all: %s", e)
        return False


def init_db() -> None:
    """Initialize database with migrations or fallback to create_all."""
    # Try Alembic migrations first
    if not run_migrations():
        # Fallback: create tables directly (for tests or fresh installs without alembic)
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
async def request_tracking_middleware(request: Request, call_next):
    """Middleware that generates request ID and tracks request lifecycle."""

    # Generate unique request ID
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))

    # Set in context variable for logging
    request_id_var.set(request_id)

    # Add to request state for potential use in handlers
    request.state.request_id = request_id

    start_time = time.time()

    # Log request start
    logger.info(
        "Request started",
        extra={
            "event": "request_start",
            "method": request.method,
            "path": request.url.path,
            "query": str(request.query_params),
            "client_ip": request.client.host if request.client else None,
        }
    )

    # Process request
    response = await call_next(request)

    # Calculate duration
    process_time = time.time() - start_time

    # Log request completion
    logger.info(
        "Request completed",
        extra={
            "event": "request_end",
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": round(process_time * 1000, 2),
        }
    )

    # Add request ID to response headers
    response.headers["X-Request-ID"] = request_id

    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception(
        "Unhandled exception",
        extra={
            "event": "unhandled_exception",
            "method": request.method,
            "path": request.url.path,
            "exception_type": type(exc).__name__,
            "exception_message": str(exc),
        }
    )
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "服务器内部错误",
            "detail": str(exc),
            "request_id": request_id_var.get(),
        },
    )


app.include_router(auth_router, prefix="/api")
app.include_router(recipes_router, prefix="/api")
app.include_router(meal_chat_router, prefix="/api")
app.include_router(meal_plans_router, prefix="/api")
app.include_router(weekly_plans_router, prefix="/api")
app.include_router(shopping_lists_router, prefix="/api")
app.include_router(intake_router, prefix="/api")
app.include_router(dashboard_router, prefix="/api")


@app.get("/", tags=["system"])
async def root():
    return {"status": "running", "version": "2.0.0"}


@app.get("/health", tags=["system"])
async def health_check():
    return {"status": "healthy"}
