from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import models, schemas
from app.crud import apply_patch, commit_or_409, get_or_404
from app.database import get_db

router = APIRouter()


@router.get("", response_model=list[schemas.ProjectRead])
def list_projects(db: Session = Depends(get_db)):
    return db.scalars(select(models.Project).order_by(models.Project.id)).all()


@router.get("/{project_id}", response_model=schemas.ProjectRead)
def get_project(project_id: int, db: Session = Depends(get_db)):
    return get_or_404(db, models.Project, project_id)


@router.post("", response_model=schemas.ProjectRead, status_code=status.HTTP_201_CREATED)
def create_project(payload: schemas.ProjectCreate, db: Session = Depends(get_db)):
    project = models.Project(**payload.model_dump())
    db.add(project)
    commit_or_409(db)
    db.refresh(project)
    return project


@router.patch("/{project_id}", response_model=schemas.ProjectRead)
def update_project(
    project_id: int, payload: schemas.ProjectUpdate, db: Session = Depends(get_db)
):
    project = get_or_404(db, models.Project, project_id)
    apply_patch(project, payload.model_dump(exclude_unset=True))
    commit_or_409(db)
    db.refresh(project)
    return project


@router.delete(
    "/{project_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response
)
def delete_project(project_id: int, db: Session = Depends(get_db)):
    project = get_or_404(db, models.Project, project_id)
    # Задачи проекта (и их комментарии) удалит PostgreSQL по ON DELETE CASCADE.
    db.delete(project)
    commit_or_409(db)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
