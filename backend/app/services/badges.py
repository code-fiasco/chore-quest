import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.models.gamification import Badge, UserBadge, WeeklyGoal
from app.models.household import Household
from app.models.task import Completion, Task, TaskInstance
from app.models.user import User
from app.services.scoring import (
    _category_sweep_achieved,
    _room_sweep_achieved,
    _tasks_due_on_date,
    build_score_breakdown,
)
from app.services.streaks import (
    calculate_current_streak,
    completion_local_date,
    completion_local_datetime,
)
from app.services.tasks import household_today

BADGE_DEFINITIONS: list[dict] = [
    {
        "name": "First Steps",
        "description": "Complete your first task",
        "icon": "first_steps",
        "is_secret": False,
    },
    {
        "name": "Hat Trick",
        "description": "Complete 3 tasks in one day",
        "icon": "hat_trick",
        "is_secret": False,
    },
    {
        "name": "Clean Sweep",
        "description": "Complete all tasks in a room in one day",
        "icon": "clean_sweep",
        "is_secret": False,
    },
    {
        "name": "Streak Starter",
        "description": "Reach a 7 day streak",
        "icon": "streak_starter",
        "is_secret": False,
    },
    {
        "name": "Dedicated",
        "description": "Reach a 30 day streak",
        "icon": "dedicated",
        "is_secret": False,
    },
    {
        "name": "Unstoppable",
        "description": "Reach a 60 day streak",
        "icon": "unstoppable",
        "is_secret": False,
    },
    {
        "name": "Legendary",
        "description": "Reach a 90 day streak",
        "icon": "legendary",
        "is_secret": False,
    },
    {
        "name": "Category King",
        "description": "Complete all tasks in a category in one day",
        "icon": "category_king",
        "is_secret": False,
    },
    {
        "name": "Overachiever",
        "description": "Exceed the weekly goal by 50%",
        "icon": "overachiever",
        "is_secret": False,
    },
    {
        "name": "Early Bird",
        "description": "Complete a task before 8am",
        "icon": "early_bird",
        "is_secret": False,
    },
    {
        "name": "Night Owl",
        "description": "Complete a task after 11pm",
        "icon": "night_owl",
        "is_secret": True,
    },
    {
        "name": "Weekend Warrior",
        "description": "Complete tasks on both days of a weekend",
        "icon": "weekend_warrior",
        "is_secret": True,
    },
    {
        "name": "Perfect Week",
        "description": "Complete all required tasks every day for a week",
        "icon": "perfect_week",
        "is_secret": True,
    },
    {
        "name": "Speed Runner",
        "description": "Complete 5 tasks within an hour",
        "icon": "speed_runner",
        "is_secret": True,
    },
]


def list_user_badges(db: Session, user: User) -> dict:
    ensure_badge_definitions(db, commit=False)
    badges = db.scalars(select(Badge).order_by(Badge.id)).all()
    earned_rows = db.scalars(
        select(UserBadge).where(UserBadge.user_id == user.id)
    ).all()
    earned_by_badge = {row.badge_id: row for row in earned_rows}

    items = []
    earned_count = 0
    for badge in badges:
        earned = earned_by_badge.get(badge.id)
        if earned is not None:
            earned_count += 1
        items.append(
            {
                "id": badge.id,
                "name": badge.name,
                "description": badge.description,
                "icon": badge.icon,
                "is_secret": badge.is_secret,
                "earned": earned is not None,
                "awarded_at": earned.awarded_at.isoformat() if earned else None,
            }
        )

    return {"badges": items, "earned_count": earned_count, "total_count": len(items)}


def ensure_badge_definitions(db: Session, *, commit: bool = True) -> None:
    for definition in BADGE_DEFINITIONS:
        existing = db.scalar(select(Badge).where(Badge.name == definition["name"]))
        if existing is None:
            db.add(Badge(**definition))
    if commit:
        db.commit()
    else:
        db.flush()


def _user_has_badge(db: Session, user_id: int, badge_name: str) -> bool:
    return (
        db.scalar(
            select(func.count())
            .select_from(UserBadge)
            .join(Badge, UserBadge.badge_id == Badge.id)
            .where(UserBadge.user_id == user_id, Badge.name == badge_name)
        )
        or 0
    ) > 0


def _award_badge(db: Session, user_id: int, badge_name: str) -> bool:
    if _user_has_badge(db, user_id, badge_name):
        return False

    badge = db.scalar(select(Badge).where(Badge.name == badge_name))
    if badge is None:
        return False

    db.add(UserBadge(user_id=user_id, badge_id=badge.id))
    return True


def _load_user_completions(
    db: Session, user: User, household: Household
) -> list[tuple[Completion, Task, TaskInstance]]:
    rows = db.scalars(
        select(Completion)
        .join(TaskInstance, Completion.task_instance_id == TaskInstance.id)
        .join(Task, TaskInstance.task_id == Task.id)
        .where(
            Completion.user_id == user.id,
            Completion.is_undone.is_(False),
            Task.household_id == household.id,
        )
        .options(
            joinedload(Completion.task_instance).joinedload(TaskInstance.task)
        )
        .order_by(Completion.completed_at)
    ).all()
    return [(row, row.task_instance.task, row.task_instance) for row in rows]


def _completions_on_date(
    completions: list[tuple[Completion, Task, TaskInstance]],
    household: Household,
    day: datetime.date,
) -> list[tuple[Completion, Task, TaskInstance]]:
    return [
        row
        for row in completions
        if completion_local_date(row[0].completed_at, household) == day
    ]


def _has_perfect_week(
    db: Session,
    user: User,
    household: Household,
    all_completions: list[tuple[Completion, Task, TaskInstance]],
) -> bool:
    today = household_today(household)
    week_start = today - datetime.timedelta(days=today.weekday())
    had_required = False

    for offset in range(7):
        day = week_start + datetime.timedelta(days=offset)
        if day > today:
            break

        required_due = [
            (task, instance)
            for task, instance in _tasks_due_on_date(db, household, day)
            if task.is_required
        ]
        if not required_due:
            continue

        had_required = True
        day_ids = {row[2].id for row in _completions_on_date(all_completions, household, day)}
        if not all(instance.id in day_ids for _, instance in required_due):
            return False

    return had_required


def check_and_award_badges(
    db: Session, user: User, household: Household, completion: Completion
) -> list[str]:
    ensure_badge_definitions(db, commit=False)
    awarded: list[str] = []

    completion = db.scalar(
        select(Completion)
        .where(Completion.id == completion.id)
        .options(joinedload(Completion.task_instance).joinedload(TaskInstance.task))
    )
    if completion is None:
        return awarded

    task = completion.task_instance.task
    local_date = completion_local_date(completion.completed_at, household)
    local_time = completion_local_datetime(completion.completed_at, household).time()
    all_completions = _load_user_completions(db, user, household)
    day_completions = _completions_on_date(all_completions, household, local_date)
    completed_instance_ids = {row[2].id for row in day_completions}

    def award(name: str) -> None:
        if _award_badge(db, user.id, name):
            awarded.append(name)

    if len(all_completions) >= 1:
        award("First Steps")

    if len(day_completions) >= 3:
        award("Hat Trick")

    if _room_sweep_achieved(db, household, local_date, task.room, completed_instance_ids):
        award("Clean Sweep")

    streak = calculate_current_streak(db, user, household)
    if streak >= 7:
        award("Streak Starter")
    if streak >= 30:
        award("Dedicated")
    if streak >= 60:
        award("Unstoppable")
    if streak >= 90:
        award("Legendary")

    if _category_sweep_achieved(
        db, household, local_date, task.category_id, completed_instance_ids
    ):
        award("Category King")

    goal = db.scalar(select(WeeklyGoal).where(WeeklyGoal.household_id == household.id))
    if goal is not None:
        weekly_score = build_score_breakdown(db, user, household)["weekly"]["total"]
        if weekly_score >= int(goal.points_target * 1.5):
            award("Overachiever")

    if local_time.hour < 8:
        award("Early Bird")

    if local_time.hour >= 23:
        award("Night Owl")

    if local_date.weekday() in (5, 6):
        saturday = local_date - datetime.timedelta(days=local_date.weekday() - 5)
        sunday = saturday + datetime.timedelta(days=1)
        if (
            _completions_on_date(all_completions, household, saturday)
            and _completions_on_date(all_completions, household, sunday)
        ):
            award("Weekend Warrior")

    if _has_perfect_week(db, user, household, all_completions):
        award("Perfect Week")

    completion_time = completion.completed_at
    if completion_time.tzinfo is None:
        completion_time = completion_time.replace(tzinfo=datetime.timezone.utc)
    window_start = completion_time - datetime.timedelta(hours=1)
    recent_count = sum(
        1
        for row, _, _ in all_completions
        if window_start <= row.completed_at <= completion_time
    )
    if recent_count >= 5:
        award("Speed Runner")

    if awarded:
        db.flush()

    return awarded
