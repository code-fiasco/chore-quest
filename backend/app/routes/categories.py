from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user, require_admin
from app.models.user import User
from app.services.tasks import (
    TaskError,
    create_category,
    delete_category,
    list_categories,
    update_category,
)

router = APIRouter(tags=["categories"])


class CategoryCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)


class CategoryUpdateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)


def _http_error(exc: TaskError) -> None:
    raise HTTPException(status_code=exc.status_code, detail=exc.message)


@router.get("")
def get_categories(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return list_categories(db, current_user)


@router.post("", status_code=201)
def post_category(
    body: CategoryCreateRequest,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    try:
        return create_category(db, admin, body.name)
    except TaskError as exc:
        _http_error(exc)


@router.put("/{category_id}")
def put_category(
    category_id: int,
    body: CategoryUpdateRequest,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    try:
        return update_category(db, admin, category_id, body.name)
    except TaskError as exc:
        _http_error(exc)


@router.delete("/{category_id}", status_code=204)
def remove_category(
    category_id: int,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    try:
        delete_category(db, admin, category_id)
    except TaskError as exc:
        _http_error(exc)
