"""Общие функции для всех роутеров: поиск записи или 404, фиксация с обработкой конфликтов БД."""

from typing import TypeVar

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import Base

ModelT = TypeVar("ModelT", bound=Base)

# Понятные сообщения по имени нарушенного ограничения (имена заданы в миграции).
CONSTRAINT_MESSAGES = {
    "uq_users_email": "User with this email already exists",
    "uq_labels_name": "Label with this name already exists",
    "fk_tasks_project_id_projects": "Project with this id does not exist",
    "fk_tasks_assignee_id_users": "User (assignee) with this id does not exist",
    "fk_tasks_label_id_labels": "Label with this id does not exist",
    "fk_comments_task_id_tasks": "Task with this id does not exist",
    "fk_comments_author_id_users": "User (author) with this id does not exist",
}


def get_or_404(db: Session, model: type[ModelT], obj_id: int) -> ModelT:
    obj = db.get(model, obj_id)
    if obj is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{model.__name__} not found",
        )
    return obj


def commit_or_409(db: Session, detail: str | None = None) -> None:
    """Фиксирует транзакцию. Нарушение уникальности или внешнего ключа превращается в 409.

    Текст исключения PostgreSQL наружу не отдаётся — только понятное сообщение.
    """
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        if detail is None:
            diag = getattr(exc.orig, "diag", None)
            constraint = getattr(diag, "constraint_name", None)
            detail = CONSTRAINT_MESSAGES.get(
                constraint, "Duplicate value or invalid reference"
            )
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=detail) from exc


def apply_patch(obj: Base, data: dict) -> None:
    """PATCH меняет только переданные поля (data получено через exclude_unset=True)."""
    for field, value in data.items():
        setattr(obj, field, value)
