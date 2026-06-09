import random
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.gamification import DailyChallenge
from app.models.household import Household
from app.models.task import Completion, Task, TaskInstance
from app.models.user import User
from app.services.tasks import ensure_current_instance, household_today

CHALLENGE_COUNT = 3
CHALLENGE_BONUS_PERCENT = 0.50


class ChallengeError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


def get_challenge_task_ids(
    db: Session, household_id: int, challenge_date: date
) -> set[int]:
    rows = db.scalars(
        select(DailyChallenge.task_id).where(
            DailyChallenge.household_id == household_id,
            DailyChallenge.challenge_date == challenge_date,
        )
    ).all()
    return set(rows)


def challenge_bonus_for_completion(
    db: Session, household_id: int, task_id: int, local_date: date, base_points: int
) -> int:
    if task_id in get_challenge_task_ids(db, household_id, local_date):
        return int(base_points * CHALLENGE_BONUS_PERCENT)
    return 0


def generate_daily_challenges(
    db: Session, household_id: int, challenge_date: date | None = None
) -> list[DailyChallenge]:
    household = db.get(Household, household_id)
    if household is None:
        raise ChallengeError("Household not found", status_code=404)

    target_date = challenge_date or household_today(household)

    existing = db.scalars(
        select(DailyChallenge)
        .where(
            DailyChallenge.household_id == household_id,
            DailyChallenge.challenge_date == target_date,
        )
        .options(joinedload(DailyChallenge.task))
    ).all()
    if existing:
        return list(existing)

    tasks = list(
        db.scalars(select(Task).where(Task.household_id == household_id)).all()
    )
    if not tasks:
        return []

    count = min(CHALLENGE_COUNT, len(tasks))
    selected = random.sample(tasks, count)

    challenges = [
        DailyChallenge(
            household_id=household_id,
            challenge_date=target_date,
            task_id=task.id,
        )
        for task in selected
    ]
    db.add_all(challenges)
    db.flush()
    return challenges


def ensure_today_challenges(db: Session, household: Household) -> list[DailyChallenge]:
    today = household_today(household)
    challenges = generate_daily_challenges(db, household.id, today)
    db.commit()
    return challenges


def _task_completion_status(
    db: Session, user: User, task: Task, household: Household, today: date
) -> dict:
    instance = ensure_current_instance(db, task, household)
    user_completion = db.scalar(
        select(Completion).where(
            Completion.user_id == user.id,
            Completion.task_instance_id == instance.id,
            Completion.is_undone.is_(False),
        )
    )

    completed_by = None
    if instance.completed_by_id is not None:
        completer = db.get(User, instance.completed_by_id)
        if completer is not None:
            completed_by = {
                "id": completer.id,
                "display_name": completer.display_name,
                "avatar": completer.avatar,
            }

    return {
        "task_id": task.id,
        "task_name": task.name,
        "description": task.description,
        "room": task.room.value,
        "base_points": task.base_points,
        "challenge_bonus_percent": int(CHALLENGE_BONUS_PERCENT * 100),
        "task_instance_id": instance.id,
        "is_locked": instance.is_locked,
        "is_completed": user_completion is not None,
        "is_done": instance.is_locked,
        "completed_by": completed_by,
        "completed_at": (
            user_completion.completed_at.isoformat() if user_completion else None
        ),
    }


def ensure_today_challenge_ids(db: Session, household: Household) -> set[int]:
    """Ensure today's challenges exist and return their task IDs."""
    today = household_today(household)
    generate_daily_challenges(db, household.id, today)
    return get_challenge_task_ids(db, household.id, today)


def get_today_challenges(db: Session, user: User) -> dict:
    household = db.get(Household, user.household_id)
    if household is None:
        raise ChallengeError("Household not found", status_code=404)

    today = household_today(household)
    challenges = generate_daily_challenges(db, household.id, today)
    db.flush()

    task_items = []
    for challenge in challenges:
        task = db.get(Task, challenge.task_id)
        if task is None:
            continue
        task_items.append(_task_completion_status(db, user, task, household, today))

    db.commit()
    return {
        "date": today.isoformat(),
        "challenges": task_items,
    }
