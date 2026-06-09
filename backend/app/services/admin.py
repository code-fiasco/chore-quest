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


def master_reset(db: Session, user: User) -> dict:
    household = db.get(Household, user.household_id)
    if household is None:
        raise AdminError("Household not found", status_code=404)

    household_id = household.id
    task_ids = list(
        db.scalars(select(Task.id).where(Task.household_id == household_id)).all()
    )

    if task_ids:
        instance_ids = list(
            db.scalars(
                select(TaskInstance.id).where(TaskInstance.task_id.in_(task_ids))
            ).all()
        )
        if instance_ids:
            db.execute(
                delete(Completion).where(Completion.task_instance_id.in_(instance_ids))
            )
        db.execute(delete(TaskInstance).where(TaskInstance.task_id.in_(task_ids)))
        db.execute(delete(Task).where(Task.household_id == household_id))

    member_ids = list(
        db.scalars(select(User.id).where(User.household_id == household_id)).all()
    )
    if member_ids:
        db.execute(delete(UserBadge).where(UserBadge.user_id.in_(member_ids)))
        db.execute(delete(Leaderboard).where(Leaderboard.user_id.in_(member_ids)))

    db.execute(delete(DailyChallenge).where(DailyChallenge.household_id == household_id))
    db.execute(delete(WeeklyGoal).where(WeeklyGoal.household_id == household_id))
    db.commit()

    return {"message": "Household game data has been reset"}
