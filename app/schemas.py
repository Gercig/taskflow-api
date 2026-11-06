"""Pydantic-схемы: HTTP-контракт API.

Для каждого ресурса три схемы:
- *Create — тело POST (обязательные поля обязательны);
- *Update — тело PATCH (все поля необязательны);
- *Read   — ответ сервера.

extra="forbid": если клиент пришлёт лишнее поле (например, id или created_at),
запрос будет отклонён с кодом 422.
"""

from datetime import datetime
from typing import Annotated, ClassVar, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

Role = Literal["operator", "admin"]
TaskStatus = Literal["open", "in_progress", "done"]
TaskPriority = Literal["low", "medium", "high"]

Email = Annotated[str, Field(max_length=255, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")]
Color = Annotated[str, Field(pattern=r"^#[0-9A-Fa-f]{6}$")]
Id = Annotated[int, Field(gt=0)]


class InputModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class PatchModel(InputModel):
    """Базовая схема PATCH: запрещает явный null для обязательных колонок."""

    not_null_fields: ClassVar[tuple[str, ...]] = ()

    @model_validator(mode="after")
    def check_not_null(self):
        for name in self.not_null_fields:
            if name in self.model_fields_set and getattr(self, name) is None:
                raise ValueError(f"Field '{name}' cannot be null")
        return self


class ReadModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ---------- users ----------
class UserCreate(InputModel):
    email: Email
    display_name: str = Field(min_length=1, max_length=255)
    role: Role = "operator"


class UserUpdate(PatchModel):
    not_null_fields = ("email", "display_name", "role")

    email: Email | None = None
    display_name: str | None = Field(default=None, min_length=1, max_length=255)
    role: Role | None = None


class UserRead(ReadModel):
    id: int
    email: str
    display_name: str
    role: str
    created_at: datetime


# ---------- projects ----------
class ProjectCreate(InputModel):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = None


class ProjectUpdate(PatchModel):
    not_null_fields = ("name",)

    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None


class ProjectRead(ReadModel):
    id: int
    name: str
    description: str | None
    created_at: datetime


# ---------- labels ----------
class LabelCreate(InputModel):
    name: str = Field(min_length=1, max_length=64)
    color: Color = "#6b7280"


class LabelUpdate(PatchModel):
    not_null_fields = ("name", "color")

    name: str | None = Field(default=None, min_length=1, max_length=64)
    color: Color | None = None


class LabelRead(ReadModel):
    id: int
    name: str
    color: str


# ---------- tasks ----------
class TaskCreate(InputModel):
    project_id: Id
    assignee_id: Id | None = None
    label_id: Id | None = None
    title: str = Field(min_length=1, max_length=200)
    description: str | None = None
    status: TaskStatus = "open"
    priority: TaskPriority = "medium"


class TaskUpdate(PatchModel):
    not_null_fields = ("project_id", "title", "status", "priority")

    project_id: Id | None = None
    assignee_id: Id | None = None
    label_id: Id | None = None
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    status: TaskStatus | None = None
    priority: TaskPriority | None = None


class TaskRead(ReadModel):
    id: int
    project_id: int
    assignee_id: int | None
    label_id: int | None
    title: str
    description: str | None
    status: str
    priority: str
    created_at: datetime
    updated_at: datetime


# ---------- comments ----------
class CommentCreate(InputModel):
    task_id: Id
    author_id: Id
    body: str = Field(min_length=1)


class CommentUpdate(PatchModel):
    """У комментария меняется только текст; задача и автор остаются прежними."""

    not_null_fields = ("body",)

    body: str | None = Field(default=None, min_length=1)


class CommentRead(ReadModel):
    id: int
    task_id: int
    author_id: int
    body: str
    created_at: datetime
