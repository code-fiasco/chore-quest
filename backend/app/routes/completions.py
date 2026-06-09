from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.services.scoring import (
    ScoringError,
    complete_task_instance,
    undo_task_instance,
)

router = APIRouter(tags=["completions"])


def _http_error(exc: ScoringError) -> None:
    raise HTTPException(status_code=exc.status_code, detail=exc.message)


@router.post("/tasks/{task_instance_id}/complete")
def complete_instance(
    task_instance_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return complete_task_instance(db, current_user, task_instance_id)
    except ScoringError as exc:
        _http_error(exc)


@router.post("/tasks/{task_instance_id}/undo")
def undo_instance(
    task_instance_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return undo_task_instance(db, current_user, task_instance_id)
    except ScoringError as exc:
        _http_error(exc)
