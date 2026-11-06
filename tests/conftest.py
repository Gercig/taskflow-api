"""Общие фикстуры тестов.

Тесты работают с настоящим PostgreSQL: адрес берётся из DATABASE_URL,
схема создаётся миграциями (alembic upgrade head) до запуска pytest.
"""

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.database import engine
from app.main import app


@pytest.fixture()
def client() -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def clean_database() -> Iterator[None]:
    """После каждого теста очищаем таблицы, чтобы тесты не влияли друг на друга."""
    yield
    with engine.begin() as connection:
        connection.execute(
            text("TRUNCATE comments, tasks, labels, projects, users RESTART IDENTITY CASCADE")
        )
