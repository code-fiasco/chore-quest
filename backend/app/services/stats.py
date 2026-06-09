import datetime
from collections import Counter

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.models.gamification import UserBadge
from app.models.household import Household
from app.models.task import Completion, Task, TaskInstance
from app.models.user import User
from app.services.scoring import build_score_breakdown
from app.services.streaks import calculate_current_streak
from app.services.tasks import ensure_current_instance, household_today


def _week_start(day: datetime.date) -> datetime.date:
    return day - datetime.timedelta(days=day.weekday())


def get_user_stats(db: Session, user: User) -> dict:
    household = db.get(Household, user.household_id)
    if household is None:
        return {}

    completions = db.scalars(
        select(Completion)
        .join(TaskInstance, Completion.task_instance_id == TaskInstance.id)
        .join(Task, TaskInstance.task_id == Task.id)
        .where(
            Completion.user_id == user.id,
            Completion.is_undone.is_(False),
            Task.household_id == household.id,
        )
        .options(
            joinedload(Completion.task_instance).joinedload(TaskInstance.task).joinedload(Task.category)
        )
    ).all()

    room_counts: Counter[str] = Counter()
    category_counts: Counter[str] = Counter()
    for completion in completions:
        task = completion.task_instance.task
        room_counts[task.room.value] += 1
        category_counts[task.category.name] += 1

    favourite_room = room_counts.most_common(1)[0][0] if room_counts else None
    best_category = category_counts.most_common(1)[0][0] if category_counts else None

    today = household_today(household)
    week_start = _week_start(today)
    week_end = week_start + datetime.timedelta(days=6)

    tasks = db.scalars(select(Task).where(Task.household_id == household.id)).all()
    due_this_week = 0
    completed_this_week = 0
    for task in tasks:
        instance = ensure_current_instance(db, task, household)
        if instance.period_start <= week_end and instance.period_end >= week_start:
            due_this_week += 1
            if instance.is_locked:
                completed_this_week += 1

    weekly_rate = (
        round((completed_this_week / due_this_week) * 100) if due_this_week else 0
    )

    badge_count = db.scalar(
        select(func.count())
        .select_from(UserBadge)
        .where(UserBadge.user_id == user.id)
    ) or 0

    breakdown = build_score_breakdown(db, user, household)

    return {
        "streak": calculate_current_streak(db, user, household),
        "total_completions": len(completions),
        "favourite_room": favourite_room,
        "best_category": best_category,
        "weekly_completion_rate": weekly_rate,
        "badges_earned": badge_count,
        "points": {
            "daily": breakdown["daily"]["total"],
            "weekly": breakdown["weekly"]["total"],
            "monthly": breakdown["monthly"]["total"],
            "lifetime": breakdown["lifetime"]["total"],
        },
    }
