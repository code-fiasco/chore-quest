import datetime
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.household import Household
from app.models.task import Completion, Task, TaskInstance
from app.models.user import User
from app.services.challenges import challenge_bonus_for_completion, ensure_today_challenge_ids
from app.services.streaks import (
    calculate_current_streak,
    completion_local_date,
    streak_milestone_bonus_for_date,
)
from app.services.tasks import household_today


class ScoringError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


@dataclass
class CompletionRecord:
    completion: Completion
    task: Task
    instance: TaskInstance
    local_date: datetime.date


@dataclass
class PeriodExtras:
    deep_clean: int = 0
    streak_milestone: int = 0
    weekly_goal: int = 0


@dataclass
class ScoreBreakdown:
    base_points: int = 0
    room_sweep_bonus: int = 0
    category_sweep_bonus: int = 0
    deep_clean_bonus: int = 0
    weekly_goal_bonus: int = 0
    streak_milestone_bonus: int = 0

    @property
    def total(self) -> int:
        return (
            self.base_points
            + self.room_sweep_bonus
            + self.category_sweep_bonus
            + self.deep_clean_bonus
            + self.weekly_goal_bonus
            + self.streak_milestone_bonus
        )


def _now_utc() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc)


def _week_start(day: datetime.date) -> datetime.date:
    return day - datetime.timedelta(days=day.weekday())


def _month_start(day: datetime.date) -> datetime.date:
    return day.replace(day=1)


def _load_household_instance(
    db: Session, task_instance_id: int, household_id: int
) -> TaskInstance:
    instance = db.scalar(
        select(TaskInstance)
        .where(TaskInstance.id == task_instance_id)
        .options(joinedload(TaskInstance.task))
    )
    if instance is None or instance.task.household_id != household_id:
        raise ScoringError("Task instance not found", status_code=404)
    return instance


def _load_active_completions(
    db: Session, user: User, household: Household
) -> list[CompletionRecord]:
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
            joinedload(Completion.task_instance).joinedload(TaskInstance.task)
        )
    ).all()

    records: list[CompletionRecord] = []
    for completion in completions:
        instance = completion.task_instance
        records.append(
            CompletionRecord(
                completion=completion,
                task=instance.task,
                instance=instance,
                local_date=completion_local_date(completion.completed_at, household),
            )
        )
    return records


def _tasks_due_on_date(
    db: Session, household: Household, day: datetime.date
) -> list[tuple[Task, TaskInstance]]:
    tasks = db.scalars(
        select(Task)
        .where(Task.household_id == household.id)
        .options(joinedload(Task.category))
    ).all()

    due: list[tuple[Task, TaskInstance]] = []
    for task in tasks:
        instance = db.scalar(
            select(TaskInstance).where(
                TaskInstance.task_id == task.id,
                TaskInstance.period_start <= day,
                TaskInstance.period_end >= day,
            )
        )
        if instance is not None:
            due.append((task, instance))
    return due


def _room_sweep_achieved(
    db: Session,
    household: Household,
    day: datetime.date,
    room,
    completed_instance_ids: set[int],
) -> bool:
    room_tasks = [
        (task, instance)
        for task, instance in _tasks_due_on_date(db, household, day)
        if task.room == room
    ]
    if not room_tasks:
        return False
    return all(instance.id in completed_instance_ids for _, instance in room_tasks)


def _category_sweep_achieved(
    db: Session,
    household: Household,
    day: datetime.date,
    category_id: int,
    completed_instance_ids: set[int],
) -> bool:
    category_tasks = [
        (task, instance)
        for task, instance in _tasks_due_on_date(db, household, day)
        if task.category_id == category_id
    ]
    if not category_tasks:
        return False
    return all(instance.id in completed_instance_ids for _, instance in category_tasks)


def _weekly_goal_achieved(
    db: Session,
    household: Household,
    week_start: datetime.date,
    week_end: datetime.date,
    completed_instance_ids: set[int],
) -> bool:
    required_tasks = db.scalars(
        select(Task).where(
            Task.household_id == household.id,
            Task.is_required.is_(True),
        )
    ).all()

    for task in required_tasks:
        instance = db.scalar(
            select(TaskInstance).where(
                TaskInstance.task_id == task.id,
                TaskInstance.period_start <= week_end,
                TaskInstance.period_end >= week_start,
            )
        )
        if instance is None or instance.id not in completed_instance_ids:
            return False
    return bool(required_tasks)


def recalculate_user_scores(db: Session, user: User, household: Household) -> None:
    """Recalculate points_awarded on every active completion from scratch."""
    records = _load_active_completions(db, user, household)

    by_day: dict[datetime.date, list[CompletionRecord]] = {}
    for record in records:
        by_day.setdefault(record.local_date, []).append(record)

    for day, day_records in by_day.items():
        completed_ids = {r.instance.id for r in day_records}

        for record in day_records:
            base = record.task.base_points
            room_bonus = 0
            category_bonus = 0

            if _room_sweep_achieved(
                db, household, day, record.task.room, completed_ids
            ):
                room_bonus = int(base * 0.5)

            if _category_sweep_achieved(
                db,
                household,
                day,
                record.task.category_id,
                completed_ids,
            ):
                category_bonus = int(base * 0.3)

            challenge_bonus = challenge_bonus_for_completion(
                db,
                household.id,
                record.task.id,
                day,
                base,
            )
            record.completion.points_awarded = (
                base + room_bonus + category_bonus + challenge_bonus
            )


def _sum_completion_points(
    records: list[CompletionRecord],
    start: datetime.date,
    end: datetime.date,
) -> int:
    return sum(
        r.completion.points_awarded
        for r in records
        if start <= r.local_date <= end
    )


def _extras_for_range(
    daily_extras: dict[datetime.date, PeriodExtras],
    weekly_extras: dict[datetime.date, PeriodExtras],
    start: datetime.date,
    end: datetime.date,
    include_weekly: bool,
) -> ScoreBreakdown:
    breakdown = ScoreBreakdown()
    for day, extras in daily_extras.items():
        if start <= day <= end:
            breakdown.deep_clean_bonus += extras.deep_clean
            breakdown.streak_milestone_bonus += extras.streak_milestone

    if include_weekly:
        for week_start, extras in weekly_extras.items():
            week_end = week_start + datetime.timedelta(days=6)
            if week_start <= end and week_end >= start:
                breakdown.weekly_goal_bonus += extras.weekly_goal

    return breakdown


def build_score_breakdown(
    db: Session,
    user: User,
    household: Household,
    *,
    as_of: datetime.date | None = None,
) -> dict:
    records = _load_active_completions(db, user, household)
    today = as_of or household_today(household)
    week_start = _week_start(today)
    week_end = week_start + datetime.timedelta(days=6)
    month_start = _month_start(today)
    if today.month == 12:
        month_end = datetime.date(today.year, 12, 31)
    else:
        month_end = datetime.date(today.year, today.month + 1, 1) - datetime.timedelta(
            days=1
        )

    by_day: dict[datetime.date, list[CompletionRecord]] = {}
    for record in records:
        by_day.setdefault(record.local_date, []).append(record)

    daily_extras: dict[datetime.date, PeriodExtras] = {}
    weekly_extras: dict[datetime.date, PeriodExtras] = {}

    for day, day_records in by_day.items():
        completed_ids = {r.instance.id for r in day_records}
        rooms = {r.task.room for r in day_records}
        extras = PeriodExtras()
        if len(rooms) >= 3:
            extras.deep_clean = 20
        extras.streak_milestone = streak_milestone_bonus_for_date(
            db, user, household, day
        )
        daily_extras[day] = extras

        week_start_day = _week_start(day)
        if week_start_day not in weekly_extras:
            week_completed = {
                r.instance.id
                for r in records
                if _week_start(r.local_date) == week_start_day
            }
            week_extras = PeriodExtras()
            if _weekly_goal_achieved(
                db,
                household,
                week_start_day,
                week_start_day + datetime.timedelta(days=6),
                week_completed,
            ):
                week_extras.weekly_goal = 100
            weekly_extras[week_start_day] = week_extras

    def period_score(start: datetime.date, end: datetime.date, weekly: bool) -> dict:
        in_period = [r for r in records if start <= r.local_date <= end]
        base = sum(r.task.base_points for r in in_period)
        completion_points = sum(r.completion.points_awarded for r in in_period)
        room_bonus = 0
        category_bonus = 0
        for day, day_records in by_day.items():
            if not (start <= day <= end):
                continue
            completed_ids = {r.instance.id for r in day_records}
            for record in day_records:
                if not (start <= record.local_date <= end):
                    continue
                b = record.task.base_points
                if _room_sweep_achieved(
                    db, household, day, record.task.room, completed_ids
                ):
                    room_bonus += int(b * 0.5)
                if _category_sweep_achieved(
                    db,
                    household,
                    day,
                    record.task.category_id,
                    completed_ids,
                ):
                    category_bonus += int(b * 0.3)

        extras = _extras_for_range(
            daily_extras, weekly_extras, start, end, include_weekly=weekly
        )
        extras.base_points = base
        extras.room_sweep_bonus = room_bonus
        extras.category_sweep_bonus = category_bonus
        challenge_bonus = max(
            0, completion_points - base - room_bonus - category_bonus
        )
        non_completion_extras = (
            extras.deep_clean_bonus
            + extras.streak_milestone_bonus
            + (extras.weekly_goal_bonus if weekly else 0)
        )

        return {
            "total": completion_points + non_completion_extras,
            "base_points": extras.base_points,
            "bonuses": {
                "room_sweep": extras.room_sweep_bonus,
                "category_sweep": extras.category_sweep_bonus,
                "challenge": challenge_bonus,
                "deep_clean": extras.deep_clean_bonus,
                "weekly_goal": extras.weekly_goal_bonus,
                "streak_milestone": extras.streak_milestone_bonus,
            },
        }

    lifetime_start = datetime.date(2000, 1, 1)
    return {
        "user_id": user.id,
        "display_name": user.display_name,
        "streak": {
            "current": calculate_current_streak(db, user, household),
        },
        "daily": period_score(today, today, weekly=False),
        "weekly": period_score(week_start, week_end, weekly=True),
        "monthly": period_score(month_start, month_end, weekly=True),
        "lifetime": period_score(lifetime_start, today, weekly=True),
    }


def get_household_scores(db: Session, user: User) -> list[dict]:
    household = db.get(Household, user.household_id)
    if household is None:
        raise ScoringError("Household not found", status_code=404)

    members = db.scalars(
        select(User).where(User.household_id == household.id)
    ).all()

    results = []
    for member in members:
        breakdown = build_score_breakdown(db, member, household)
        results.append(
            {
                "user_id": member.id,
                "display_name": member.display_name,
                "avatar": member.avatar,
                "daily": breakdown["daily"]["total"],
                "weekly": breakdown["weekly"]["total"],
                "monthly": breakdown["monthly"]["total"],
                "lifetime": breakdown["lifetime"]["total"],
                "streak": breakdown["streak"]["current"],
            }
        )
    return results


def complete_task_instance(
    db: Session, user: User, task_instance_id: int
) -> dict:
    instance = _load_household_instance(db, task_instance_id, user.household_id)
    household = db.get(Household, user.household_id)
    if household is None:
        raise ScoringError("Household not found", status_code=404)

    if instance.is_locked and instance.completed_by_id != user.id:
        raise ScoringError(
            "This task instance has already been completed by another user",
            status_code=409,
        )

    existing = db.scalar(
        select(Completion).where(
            Completion.task_instance_id == instance.id,
            Completion.user_id == user.id,
            Completion.is_undone.is_(False),
        )
    )
    if existing is not None:
        raise ScoringError("You have already completed this task instance", status_code=409)

    now = _now_utc()
    completion = Completion(
        user_id=user.id,
        task_instance_id=instance.id,
        points_awarded=instance.task.base_points,
        completed_at=now,
        is_undone=False,
    )
    db.add(completion)

    instance.is_locked = True
    instance.completed_by_id = user.id
    instance.completed_at = now

    db.flush()

    # Challenges must exist before scoring so bonus applies even if the
    # challenges endpoint was never called today.
    ensure_today_challenge_ids(db, household)

    recalculate_user_scores(db, user, household)

    from app.services.badges import check_and_award_badges

    new_badges = check_and_award_badges(db, user, household, completion)

    db.commit()
    db.refresh(completion)

    return {
        "completion_id": completion.id,
        "task_instance_id": instance.id,
        "points_awarded": completion.points_awarded,
        "completed_at": completion.completed_at.isoformat(),
        "badges_earned": new_badges,
        "scores": build_score_breakdown(db, user, household),
    }


def undo_task_instance(db: Session, user: User, task_instance_id: int) -> dict:
    instance = _load_household_instance(db, task_instance_id, user.household_id)
    household = db.get(Household, user.household_id)
    if household is None:
        raise ScoringError("Household not found", status_code=404)

    completion = db.scalar(
        select(Completion).where(
            Completion.task_instance_id == instance.id,
            Completion.user_id == user.id,
            Completion.is_undone.is_(False),
        )
    )
    if completion is None:
        raise ScoringError(
            "No active completion found for this task instance", status_code=404
        )

    completion.is_undone = True

    if instance.completed_by_id == user.id:
        instance.is_locked = False
        instance.completed_by_id = None
        instance.completed_at = None

    ensure_today_challenge_ids(db, household)
    recalculate_user_scores(db, user, household)
    db.commit()

    return {
        "task_instance_id": instance.id,
        "undone": True,
        "scores": build_score_breakdown(db, user, household),
    }
