from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_admin
from app.models.user import User
from app.services.admin import AdminError, master_reset, reset_progress

router = APIRouter(tags=["admin"])


@router.post("/reset")
def reset_household(
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    try:
        return master_reset(db, admin)
    except AdminError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)


@router.post("/reset/progress")
def reset_household_progress(
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    try:
        return reset_progress(db, admin)
    except AdminError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)
