from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user, require_admin
from app.models.user import User
from app.services.tasks import (
    TaskError,
    create_task,
    delete_task,
    list_tasks_grouped,
    reorder_tasks,
    update_task,
)

router = APIRouter(tags=["tasks"])

ROOM_VALUES = Literal[
    "Kitchen",
    "Bathroom",
    "Bedroom",
    "Living Room",
    "Dining Room",
    "Hallway",
    "Other",
]
FREQUENCY_VALUES = Literal["daily", "weekly", "monthly"]


class TaskCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    frequency: FREQUENCY_VALUES
    base_points: int = Field(default=10, ge=1)
    category_id: int
    room: ROOM_VALUES
    is_required: bool = True


class TaskReorderRequest(BaseModel):
    task_ids: list[int] = Field(min_length=1)


class TaskUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    frequency: FREQUENCY_VALUES | None = None
    base_points: int | None = Field(default=None, ge=1)
    category_id: int | None = None
    room: ROOM_VALUES | None = None
    is_required: bool | None = None


def _http_error(exc: TaskError) -> None:
    raise HTTPException(status_code=exc.status_code, detail=exc.message)


@router.get("")
def get_tasks(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return list_tasks_grouped(db, current_user)
    except TaskError as exc:
        _http_error(exc)


@router.post("", status_code=201)
def post_task(
    body: TaskCreateRequest,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    try:
        return create_task(
            db,
            admin,
            name=body.name,
            description=body.description,
            frequency=body.frequency,
            base_points=body.base_points,
            category_id=body.category_id,
            room=body.room,
            is_required=body.is_required,
        )
    except TaskError as exc:
        _http_error(exc)


@router.put("/reorder")
def put_task_reorder(
    body: TaskReorderRequest,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    try:
        return reorder_tasks(db, admin, body.task_ids)
    except TaskError as exc:
        _http_error(exc)


@router.put("/{task_id}")
def put_task(
    task_id: int,
    body: TaskUpdateRequest,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    try:
        return update_task(
            db,
            admin,
            task_id,
            name=body.name,
            description=body.description,
            frequency=body.frequency,
            base_points=body.base_points,
            category_id=body.category_id,
            room=body.room,
            is_required=body.is_required,
        )
    except TaskError as exc:
        _http_error(exc)


@router.delete("/{task_id}", status_code=204)
def remove_task(
    task_id: int,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    try:
        delete_task(db, admin, task_id)
    except TaskError as exc:
        _http_error(exc)
