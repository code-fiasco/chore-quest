import calendar
import datetime
from zoneinfo import ZoneInfo

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.models.household import Category, Household
from app.models.task import Completion, Room, Task, TaskFrequency, TaskInstance
from app.models.user import User


class TaskError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


def household_today(household: Household) -> datetime.date:
    return datetime.datetime.now(ZoneInfo(household.timezone)).date()


def monthly_week_bounds(
    year: int, month: int, week_slot: int
) -> tuple[datetime.date, datetime.date]:
    last_day = calendar.monthrange(year, month)[1]
    week_starts = [1, 8, 15, 22]
    start_day = week_starts[week_slot - 1]
    if week_slot < 4:
        end_day = week_starts[week_slot] - 1
    else:
        end_day = last_day
    return datetime.date(year, month, start_day), datetime.date(year, month, end_day)


def monthly_week_slot(task: Task) -> int:
    return (task.id - 1) % 4 + 1


def get_period_bounds(
    task: Task, household: Household, today: datetime.date
) -> tuple[datetime.date, datetime.date]:
    if task.frequency == TaskFrequency.DAILY:
        return today, today

    if task.frequency == TaskFrequency.WEEKLY:
        monday = today - datetime.timedelta(days=today.weekday())
        return monday, monday + datetime.timedelta(days=6)

    week_slot = monthly_week_slot(task)
    return monthly_week_bounds(today.year, today.month, week_slot)


def ensure_current_instance(
    db: Session, task: Task, household: Household
) -> TaskInstance:
    today = household_today(household)
    period_start, period_end = get_period_bounds(task, household, today)

    instance = db.scalar(
        select(TaskInstance).where(
            TaskInstance.task_id == task.id,
            TaskInstance.period_start == period_start,
            TaskInstance.period_end == period_end,
        )
    )
    if instance is not None:
        return instance

    instance = TaskInstance(
        task_id=task.id,
        period_start=period_start,
        period_end=period_end,
    )
    db.add(instance)
    db.flush()
    return instance


def _get_household_category(
    db: Session, category_id: int, household_id: int
) -> Category:
    category = db.scalar(
        select(Category).where(
            Category.id == category_id,
            Category.household_id == household_id,
        )
    )
    if category is None:
        raise TaskError("Category not found", status_code=404)
    return category


def _get_household_task(db: Session, task_id: int, household_id: int) -> Task:
    task = db.scalar(
        select(Task)
        .where(Task.id == task_id, Task.household_id == household_id)
        .options(joinedload(Task.category))
    )
    if task is None:
        raise TaskError("Task not found", status_code=404)
    return task


def _parse_room(room: str) -> Room:
    try:
        return Room(room)
    except ValueError:
        valid = ", ".join(r.value for r in Room)
        raise TaskError(f"Room must be one of: {valid}")


def _parse_frequency(frequency: str) -> TaskFrequency:
    try:
        return TaskFrequency(frequency)
    except ValueError:
        raise TaskError("Frequency must be daily, weekly, or monthly")


def _user_instance_status(
    db: Session, user: User, instance: TaskInstance
) -> dict:
    completion = db.scalar(
        select(Completion).where(
            Completion.task_instance_id == instance.id,
            Completion.user_id == user.id,
            Completion.is_undone.is_(False),
        )
    )
    return {
        "is_completed": completion is not None,
        "completed_at": completion.completed_at.isoformat() if completion else None,
    }


def instance_to_dict(instance: TaskInstance, user: User, db: Session) -> dict:
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
        "id": instance.id,
        "period_start": instance.period_start.isoformat(),
        "period_end": instance.period_end.isoformat(),
        "is_locked": instance.is_locked,
        "completed_by_id": instance.completed_by_id,
        "completed_by": completed_by,
        "completed_at": instance.completed_at.isoformat() if instance.completed_at else None,
        "user_status": _user_instance_status(db, user, instance),
    }


def task_to_dict(task: Task, instance: TaskInstance, user: User, db: Session) -> dict:
    return {
        "id": task.id,
        "name": task.name,
        "description": task.description,
        "frequency": task.frequency.value,
        "base_points": task.base_points,
        "category": {"id": task.category.id, "name": task.category.name},
        "room": task.room.value,
        "is_required": task.is_required,
        "household_id": task.household_id,
        "created_at": task.created_at.isoformat(),
        "current_instance": instance_to_dict(instance, user, db),
    }


def list_tasks_grouped(db: Session, user: User) -> dict:
    from app.services.challenges import ensure_today_challenge_ids

    household = db.get(Household, user.household_id)
    if household is None:
        raise TaskError("Household not found", status_code=404)

    challenge_task_ids = ensure_today_challenge_ids(db, household)

    tasks = db.scalars(
        select(Task)
        .where(Task.household_id == user.household_id)
        .options(joinedload(Task.category))
        .order_by(Task.name)
    ).all()

    grouped: dict[str, list] = {"daily": [], "weekly": [], "monthly": []}
    for task in tasks:
        if task.id in challenge_task_ids:
            continue
        instance = ensure_current_instance(db, task, household)
        grouped[task.frequency.value].append(task_to_dict(task, instance, user, db))

    db.commit()
    return grouped


def create_task(
    db: Session,
    user: User,
    *,
    name: str,
    description: str | None,
    frequency: str,
    base_points: int,
    category_id: int,
    room: str,
    is_required: bool,
) -> dict:
    name = name.strip()
    if not name:
        raise TaskError("Task name is required")

    if base_points < 1:
        raise TaskError("Base points must be at least 1")

    _get_household_category(db, category_id, user.household_id)
    parsed_frequency = _parse_frequency(frequency)
    parsed_room = _parse_room(room)

    task = Task(
        name=name,
        description=description.strip() if description else None,
        frequency=parsed_frequency,
        base_points=base_points,
        category_id=category_id,
        room=parsed_room,
        is_required=is_required,
        household_id=user.household_id,
    )
    db.add(task)
    db.flush()

    household = db.get(Household, user.household_id)
    instance = ensure_current_instance(db, task, household)
    db.commit()
    db.refresh(task)
    return task_to_dict(task, instance, user, db)


def update_task(
    db: Session,
    user: User,
    task_id: int,
    *,
    name: str | None = None,
    description: str | None = None,
    frequency: str | None = None,
    base_points: int | None = None,
    category_id: int | None = None,
    room: str | None = None,
    is_required: bool | None = None,
) -> dict:
    task = _get_household_task(db, task_id, user.household_id)

    if name is not None:
        name = name.strip()
        if not name:
            raise TaskError("Task name is required")
        task.name = name

    if description is not None:
        task.description = description.strip() if description else None

    if frequency is not None:
        task.frequency = _parse_frequency(frequency)

    if base_points is not None:
        if base_points < 1:
            raise TaskError("Base points must be at least 1")
        task.base_points = base_points

    if category_id is not None:
        _get_household_category(db, category_id, user.household_id)
        task.category_id = category_id

    if room is not None:
        task.room = _parse_room(room)

    if is_required is not None:
        task.is_required = is_required

    household = db.get(Household, user.household_id)
    instance = ensure_current_instance(db, task, household)
    db.commit()
    db.refresh(task)
    return task_to_dict(task, instance, user, db)


def delete_task(db: Session, user: User, task_id: int) -> None:
    task = _get_household_task(db, task_id, user.household_id)

    has_completions = db.scalar(
        select(func.count())
        .select_from(Completion)
        .join(TaskInstance, Completion.task_instance_id == TaskInstance.id)
        .where(TaskInstance.task_id == task.id)
    )
    if has_completions:
        raise TaskError(
            "Cannot delete a task that has completion history",
            status_code=409,
        )

    db.delete(task)
    db.commit()


def category_to_dict(category: Category) -> dict:
    return {
        "id": category.id,
        "name": category.name,
        "household_id": category.household_id,
    }


def list_categories(db: Session, user: User) -> list[dict]:
    categories = db.scalars(
        select(Category)
        .where(Category.household_id == user.household_id)
        .order_by(Category.name)
    ).all()
    return [category_to_dict(c) for c in categories]


def create_category(db: Session, user: User, name: str) -> dict:
    name = name.strip()
    if not name:
        raise TaskError("Category name is required")

    existing = db.scalar(
        select(Category).where(
            Category.household_id == user.household_id,
            func.lower(Category.name) == name.lower(),
        )
    )
    if existing:
        raise TaskError("A category with this name already exists", status_code=409)

    category = Category(name=name, household_id=user.household_id)
    db.add(category)
    db.commit()
    db.refresh(category)
    return category_to_dict(category)


def update_category(db: Session, user: User, category_id: int, name: str) -> dict:
    name = name.strip()
    if not name:
        raise TaskError("Category name is required")

    category = db.scalar(
        select(Category).where(
            Category.id == category_id,
            Category.household_id == user.household_id,
        )
    )
    if category is None:
        raise TaskError("Category not found", status_code=404)

    duplicate = db.scalar(
        select(Category).where(
            Category.household_id == user.household_id,
            func.lower(Category.name) == name.lower(),
            Category.id != category_id,
        )
    )
    if duplicate:
        raise TaskError("A category with this name already exists", status_code=409)

    category.name = name
    db.commit()
    db.refresh(category)
    return category_to_dict(category)


def delete_category(db: Session, user: User, category_id: int) -> None:
    category = db.scalar(
        select(Category).where(
            Category.id == category_id,
            Category.household_id == user.household_id,
        )
    )
    if category is None:
        raise TaskError("Category not found", status_code=404)

    task_count = db.scalar(
        select(func.count()).select_from(Task).where(Task.category_id == category_id)
    )
    if task_count:
        raise TaskError(
            "Cannot delete a category that is assigned to tasks",
            status_code=409,
        )

    db.delete(category)
    db.commit()
