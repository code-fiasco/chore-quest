from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.gamification import DailyChallenge, Leaderboard, UserBadge, WeeklyGoal
from app.models.household import Household
from app.models.task import Completion, Task, TaskInstance
from app.models.user import User


class AdminError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


def _member_ids(db: Session, household_id: int) -> list[int]:
    return list(
        db.scalars(select(User.id).where(User.household_id == household_id)).all()
    )


def _task_ids(db: Session, household_id: int) -> list[int]:
    return list(
        db.scalars(select(Task.id).where(Task.household_id == household_id)).all()
    )


def _clear_progress(db: Session, household_id: int) -> None:
    """Remove completions, instances, badges, scores, and daily challenges."""
    member_ids = _member_ids(db, household_id)
    task_ids = _task_ids(db, household_id)

    # daily_challenges references tasks — must go before task_instances/tasks are removed.
    db.execute(delete(DailyChallenge).where(DailyChallenge.household_id == household_id))

    if task_ids:
        instance_ids = list(
            db.scalars(
                select(TaskInstance.id).where(TaskInstance.task_id.in_(task_ids))
            ).all()
        )
        if instance_ids:
            # Admin-only destructive reset; normal gameplay keeps completion history (PRD §23).
            db.execute(
                delete(Completion).where(Completion.task_instance_id.in_(instance_ids))
            )
        db.execute(delete(TaskInstance).where(TaskInstance.task_id.in_(task_ids)))

    if member_ids:
        db.execute(delete(UserBadge).where(UserBadge.user_id.in_(member_ids)))
        db.execute(delete(Leaderboard).where(Leaderboard.user_id.in_(member_ids)))


def reset_progress(db: Session, user: User) -> dict:
    """Clear all progress and points but keep task definitions and weekly goal target."""
    household = db.get(Household, user.household_id)
    if household is None:
        raise AdminError("Household not found", status_code=404)

    _clear_progress(db, household.id)
    db.commit()

    return {
        "message": "Progress and points have been cleared; your tasks are unchanged"
    }


def master_reset(db: Session, user: User) -> dict:
    """Delete all game data including tasks, categories remain."""
    household = db.get(Household, user.household_id)
    if household is None:
        raise AdminError("Household not found", status_code=404)

    household_id = household.id
    _clear_progress(db, household_id)

    db.execute(delete(Task).where(Task.household_id == household_id))
    db.execute(delete(WeeklyGoal).where(WeeklyGoal.household_id == household_id))
    db.commit()

    return {"message": "Household game data has been reset"}
