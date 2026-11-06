import logging
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.config import settings
from app.database import engine, get_db
from app.logging_config import setup_logging
from app.routers import comments, labels, projects, tasks, users

setup_logging(settings.log_level)
logger = logging.getLogger("taskflow")


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    logger.info("TaskFlow API is starting (log level %s)", settings.log_level)
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        logger.info("Database connection OK")
    except SQLAlchemyError:
        logger.critical("Database is unavailable at startup: API cannot serve data")
    yield
    logger.info("TaskFlow API is shutting down")


# Таблицы здесь НЕ создаются (никакого Base.metadata.create_all):
# схема БД меняется только миграциями Alembic.
app = FastAPI(title="TaskFlow API", version="1.1.0", lifespan=lifespan)

app.include_router(users.router, prefix="/v1/users", tags=["users"])
app.include_router(projects.router, prefix="/v1/projects", tags=["projects"])
app.include_router(labels.router, prefix="/v1/labels", tags=["labels"])
app.include_router(tasks.router, prefix="/v1/tasks", tags=["tasks"])
app.include_router(comments.router, prefix="/v1/comments", tags=["comments"])


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Каждый запрос: DEBUG при начале, INFO/WARNING/ERROR по коду ответа."""
    logger.debug("-> %s %s", request.method, request.url.path)
    started = time.perf_counter()
    response = await call_next(request)
    duration_ms = (time.perf_counter() - started) * 1000
    message = "%s %s -> %s (%.1f ms)"
    args = (request.method, request.url.path, response.status_code, duration_ms)
    if response.status_code >= 500:
        logger.error(message, *args)
    elif response.status_code >= 400:
        logger.warning(message, *args)
    else:
        logger.info(message, *args)
    return response


@app.exception_handler(RequestValidationError)
async def log_validation_error(request: Request, exc: RequestValidationError):
    logger.warning("Validation error on %s %s: %s", request.method, request.url.path, exc.errors())
    return await request_validation_exception_handler(request, exc)


@app.exception_handler(Exception)
async def log_unhandled_error(request: Request, exc: Exception):
    # logger.exception пишет сообщение уровня ERROR вместе с трассировкой.
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


@app.get("/health", tags=["health"])
def health(db: Session = Depends(get_db)) -> dict[str, str]:
    """Проверяет соединение с БД: 200 — база доступна, 503 — нет."""
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        logger.error("Health check failed: database unavailable")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database unavailable",
        ) from exc
    return {"status": "ok", "database": "up"}
