from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import models, schemas
from app.crud import apply_patch, commit_or_409, get_or_404
from app.database import get_db

router = APIRouter()


@router.get("", response_model=list[schemas.TaskRead])
def list_tasks(
    project_id: int | None = None,
    task_status: schemas.TaskStatus | None = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
):
    """Список задач. Фильтры: ?project_id=1&status=open (оба необязательны)."""
    statement = select(models.Task)
    if project_id is not None:
        statement = statement.where(models.Task.project_id == project_id)
    if task_status is not None:
        statement = statement.where(models.Task.status == task_status)
    return db.scalars(statement.order_by(models.Task.id)).all()


@router.get("/{task_id}", response_model=schemas.TaskRead)
def get_task(task_id: int, db: Session = Depends(get_db)):
    return get_or_404(db, models.Task, task_id)


@router.post("", response_model=schemas.TaskRead, status_code=status.HTTP_201_CREATED)
def create_task(payload: schemas.TaskCreate, db: Session = Depends(get_db)):
    task = models.Task(**payload.model_dump())
    db.add(task)
    commit_or_409(db)
    db.refresh(task)
    return task


@router.patch("/{task_id}", response_model=schemas.TaskRead)
def update_task(task_id: int, payload: schemas.TaskUpdate, db: Session = Depends(get_db)):
    task = get_or_404(db, models.Task, task_id)
    apply_patch(task, payload.model_dump(exclude_unset=True))
    commit_or_409(db)  # updated_at обновится автоматически (onupdate=now())
    db.refresh(task)
    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def delete_task(task_id: int, db: Session = Depends(get_db)):
    task = get_or_404(db, models.Task, task_id)
    # Комментарии задачи удалит PostgreSQL по ON DELETE CASCADE.
    db.delete(task)
    commit_or_409(db)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
