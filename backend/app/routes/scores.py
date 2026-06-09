from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.household import Household
from app.models.user import User
from app.services.scoring import (
    ScoringError,
    build_score_breakdown,
    get_household_scores,
)

router = APIRouter(tags=["scores"])


def _http_error(exc: ScoringError) -> None:
    raise HTTPException(status_code=exc.status_code, detail=exc.message)


@router.get("")
def get_scores(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return {"members": get_household_scores(db, current_user)}
    except ScoringError as exc:
        _http_error(exc)


@router.get("/me")
def get_my_scores(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    household = db.get(Household, current_user.household_id)
    if household is None:
        raise HTTPException(status_code=404, detail="Household not found")
    return build_score_breakdown(db, current_user, household)
