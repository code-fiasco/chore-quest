from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_admin
from app.models.user import User
from app.services.admin import AdminError, master_reset

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
