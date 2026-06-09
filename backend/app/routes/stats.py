from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.services.stats import get_user_stats

router = APIRouter(tags=["stats"])


@router.get("")
def stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return get_user_stats(db, current_user)
