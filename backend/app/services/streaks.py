import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.household import Household
from app.models.task import Completion, Task, TaskInstance
from app.models.user import User
from app.services.tasks import household_today

STREAK_MILESTONES = (7, 30, 60, 90)


def completion_local_date(
    completed_at: datetime.datetime, household: Household
) -> datetime.date:
    return completion_local_datetime(completed_at, household).date()


def completion_local_datetime(
    completed_at: datetime.datetime, household: Household
) -> datetime.datetime:
    from zoneinfo import ZoneInfo

    tz = ZoneInfo(household.timezone)
    if completed_at.tzinfo is None:
        completed_at = completed_at.replace(tzinfo=datetime.timezone.utc)
    return completed_at.astimezone(tz)


def get_required_completion_dates(
    db: Session, user: User, household: Household
) -> set[datetime.date]:
    completions = db.scalars(
        select(Completion)
        .join(TaskInstance, Completion.task_instance_id == TaskInstance.id)
        .join(Task, TaskInstance.task_id == Task.id)
        .where(
            Completion.user_id == user.id,
            Completion.is_undone.is_(False),
            Task.is_required.is_(True),
            Task.household_id == household.id,
        )
        .options(joinedload(Completion.task_instance).joinedload(TaskInstance.task))
    ).all()

    return {
        completion_local_date(completion.completed_at, household)
        for completion in completions
    }


def calculate_current_streak(
    db: Session, user: User, household: Household
) -> int:
    dates = get_required_completion_dates(db, user, household)
    today = household_today(household)
    cursor = today if today in dates else today - datetime.timedelta(days=1)

    streak = 0
    while cursor in dates:
        streak += 1
        cursor -= datetime.timedelta(days=1)
    return streak


def streak_milestone_bonus_for_date(
    db: Session, user: User, household: Household, on_date: datetime.date
) -> int:
    """Award +50 when a required completion on on_date achieves an exact milestone."""
    dates = get_required_completion_dates(db, user, household)
    cursor = on_date if on_date in dates else on_date - datetime.timedelta(days=1)
    streak = 0
    while cursor in dates:
        streak += 1
        cursor -= datetime.timedelta(days=1)

    if on_date in dates and streak in STREAK_MILESTONES:
        return 50
    return 0
