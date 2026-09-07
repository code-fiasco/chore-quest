from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user, require_admin
from app.models.household import Household
from app.models.user import User
from app.services.badges import list_user_badges
from app.services.challenges import ChallengeError, get_today_challenges
from app.services.leaderboards import GoalError, get_leaderboards, get_weekly_goal, set_weekly_goal
from app.services.streaks import calculate_current_streak

router = APIRouter(tags=["gamification"])


class WeeklyGoalUpdate(BaseModel):
    points_target: int | None = Field(default=None, ge=1)
    daily_challenges_enabled: bool | None = None
    daily_challenge_count: int | None = Field(default=None, ge=1, le=5)


@router.get("/challenges/today")
def today_challenges(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return get_today_challenges(db, current_user)
    except ChallengeError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)


@router.get("/goals")
def get_goals(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return get_weekly_goal(db, current_user)
    except GoalError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)


@router.put("/goals")
def update_goals(
    body: WeeklyGoalUpdate,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    try:
        if (
            body.points_target is None
            and body.daily_challenges_enabled is None
            and body.daily_challenge_count is None
        ):
            raise HTTPException(status_code=400, detail="No settings to update")
        return set_weekly_goal(
            db,
            admin,
            body.points_target,
            daily_challenges_enabled=body.daily_challenges_enabled,
            daily_challenge_count=body.daily_challenge_count,
        )
    except GoalError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)


@router.get("/streaks")
def get_streaks(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    household = db.get(Household, current_user.household_id)
    if household is None:
        raise HTTPException(status_code=404, detail="Household not found")

    members = db.scalars(
        select(User).where(User.household_id == household.id).order_by(User.display_name)
    ).all()

    return {
        "members": [
            {
                "user_id": member.id,
                "display_name": member.display_name,
                "avatar": member.avatar,
                "current_streak": calculate_current_streak(db, member, household),
            }
            for member in members
        ]
    }


@router.get("/leaderboards")
def leaderboards(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return get_leaderboards(db, current_user)


@router.get("/badges")
def badges(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return list_user_badges(db, current_user)
