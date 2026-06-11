import datetime
from collections import Counter

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.models.gamification import Badge, UserBadge, WeeklyGoal
from app.models.household import Category, Household
from app.models.task import Completion, Room, Task, TaskFrequency, TaskInstance
from app.models.user import User
from app.services.challenges import get_challenge_task_ids
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
    get_required_completion_dates,
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
        "name": "Rise and Shine",
        "description": "Complete a task before 7am",
        "icon": "rise_and_shine",
        "is_secret": False,
    },
    {
        "name": "Lunchtime Hero",
        "description": "Complete 3 tasks between 12pm and 2pm",
        "icon": "lunchtime_hero",
        "is_secret": False,
    },
    {
        "name": "Daily Devotion",
        "description": "Complete all daily tasks in a single day",
        "icon": "daily_devotion",
        "is_secret": False,
    },
    {
        "name": "Weekly Warrior",
        "description": "Complete all weekly tasks in a single week",
        "icon": "weekly_warrior",
        "is_secret": False,
    },
    {
        "name": "Monthly Marvel",
        "description": "Complete all monthly tasks in a single month",
        "icon": "monthly_marvel",
        "is_secret": False,
    },
    {
        "name": "Point Hoarder",
        "description": "Accumulate 1,000 lifetime points",
        "icon": "point_hoarder",
        "is_secret": False,
    },
    {
        "name": "High Roller",
        "description": "Accumulate 5,000 lifetime points",
        "icon": "high_roller",
        "is_secret": False,
    },
    {
        "name": "Points King",
        "description": "Accumulate 10,000 lifetime points",
        "icon": "points_king",
        "is_secret": False,
    },
    {
        "name": "Points Legend",
        "description": "Accumulate 20,000 lifetime points",
        "icon": "points_legend",
        "is_secret": False,
    },
    {
        "name": "Centurion",
        "description": "Complete 100 tasks lifetime",
        "icon": "centurion",
        "is_secret": False,
    },
    {
        "name": "Five Hundred Club",
        "description": "Complete 500 tasks lifetime",
        "icon": "five_hundred_club",
        "is_secret": False,
    },
    {
        "name": "Millennium",
        "description": "Complete 1,000 tasks lifetime",
        "icon": "millennium",
        "is_secret": False,
    },
    {
        "name": "Two Thousand",
        "description": "Complete 2,000 tasks lifetime",
        "icon": "two_thousand",
        "is_secret": False,
    },
    {
        "name": "Comeback Kid",
        "description": "Restore a streak after it was broken",
        "icon": "comeback_kid",
        "is_secret": False,
    },
    {
        "name": "Helping Hand",
        "description": "Complete a task within 10 minutes of your partner",
        "icon": "helping_hand",
        "is_secret": False,
    },
    {
        "name": "Room Master: Kitchen",
        "description": "Complete every kitchen task 10 times",
        "icon": "room_master_kitchen",
        "is_secret": False,
    },
    {
        "name": "Room Master: Bathroom",
        "description": "Complete every bathroom task 10 times",
        "icon": "room_master_bathroom",
        "is_secret": False,
    },
    {
        "name": "Tidy Tyrant",
        "description": "Complete all tidying category tasks in a week",
        "icon": "tidy_tyrant",
        "is_secret": False,
    },
    {
        "name": "Chef's Kiss",
        "description": "Complete all cooking category tasks in a week",
        "icon": "chefs_kiss",
        "is_secret": False,
    },
    {
        "name": "Laundry Legend",
        "description": "Complete 5 laundry tasks in a week",
        "icon": "laundry_legend",
        "is_secret": False,
    },
    {
        "name": "Consistent",
        "description": "Complete at least one task every day for a month",
        "icon": "consistent",
        "is_secret": False,
    },
    {
        "name": "Overachiever II",
        "description": "Exceed the weekly goal by 100%",
        "icon": "overachiever_ii",
        "is_secret": False,
    },
    {
        "name": "Double Trouble",
        "description": "Both household members complete tasks on the same day for 7 days straight",
        "icon": "double_trouble",
        "is_secret": False,
    },
    {
        "name": "Hat Trick Hero",
        "description": "Complete 3 daily challenges in a single day",
        "icon": "hat_trick_hero",
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
    {
        "name": "Insomniac",
        "description": "Complete a task between 2am and 4am",
        "icon": "insomniac",
        "is_secret": True,
    },
    {
        "name": "New Year New Me",
        "description": "Complete a task on January 1st",
        "icon": "new_year_new_me",
        "is_secret": True,
    },
    {
        "name": "Birthday Chores",
        "description": "Complete a task on your account anniversary date",
        "icon": "birthday_chores",
        "is_secret": True,
    },
    {
        "name": "The Completionist",
        "description": "Earn every other non-secret badge",
        "icon": "the_completionist",
        "is_secret": True,
    },
]

VISIBLE_BADGE_NAMES = {d["name"] for d in BADGE_DEFINITIONS if not d["is_secret"]}
LIFETIME_TASK_MILESTONES = (
    ("Centurion", 100),
    ("Five Hundred Club", 500),
    ("Millennium", 1000),
    ("Two Thousand", 2000),
)
LIFETIME_POINT_MILESTONES = (
    ("Point Hoarder", 1000),
    ("High Roller", 5000),
    ("Points King", 10000),
    ("Points Legend", 20000),
)


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
        else:
            existing.description = definition["description"]
            existing.icon = definition["icon"]
            existing.is_secret = definition["is_secret"]
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


def _week_start(day: datetime.date) -> datetime.date:
    return day - datetime.timedelta(days=day.weekday())


def _month_end(day: datetime.date) -> datetime.date:
    if day.month == 12:
        return datetime.date(day.year, 12, 31)
    return datetime.date(day.year, day.month + 1, 1) - datetime.timedelta(days=1)


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
            joinedload(Completion.task_instance)
            .joinedload(TaskInstance.task)
            .joinedload(Task.category)
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


def _completions_in_range(
    completions: list[tuple[Completion, Task, TaskInstance]],
    household: Household,
    start: datetime.date,
    end: datetime.date,
) -> list[tuple[Completion, Task, TaskInstance]]:
    return [
        row
        for row in completions
        if start
        <= completion_local_date(row[0].completed_at, household)
        <= end
    ]


def _completed_instance_ids(
    completions: list[tuple[Completion, Task, TaskInstance]],
) -> set[int]:
    return {row[2].id for row in completions}


def _frequency_period_sweep(
    db: Session,
    household: Household,
    frequency: TaskFrequency,
    period_start: datetime.date,
    period_end: datetime.date,
    completed_instance_ids: set[int],
) -> bool:
    tasks = db.scalars(
        select(Task).where(
            Task.household_id == household.id,
            Task.frequency == frequency,
        )
    ).all()
    if not tasks:
        return False

    for task in tasks:
        instance = db.scalar(
            select(TaskInstance).where(
                TaskInstance.task_id == task.id,
                TaskInstance.period_start <= period_end,
                TaskInstance.period_end >= period_start,
            )
        )
        if instance is None or instance.id not in completed_instance_ids:
            return False
    return True


def _category_by_name(db: Session, household: Household, name: str) -> Category | None:
    return db.scalar(
        select(Category).where(
            Category.household_id == household.id,
            Category.name == name,
        )
    )


def _category_week_sweep(
    db: Session,
    household: Household,
    category_name: str,
    week_start: datetime.date,
    week_end: datetime.date,
    completed_instance_ids: set[int],
) -> bool:
    category = _category_by_name(db, household, category_name)
    if category is None:
        return False

    tasks = db.scalars(
        select(Task).where(
            Task.household_id == household.id,
            Task.category_id == category.id,
        )
    ).all()
    if not tasks:
        return False

    for task in tasks:
        instance = db.scalar(
            select(TaskInstance).where(
                TaskInstance.task_id == task.id,
                TaskInstance.period_start <= week_end,
                TaskInstance.period_end >= week_start,
            )
        )
        if instance is None or instance.id not in completed_instance_ids:
            return False
    return True


def _lunchtime_count_on_date(
    day_completions: list[tuple[Completion, Task, TaskInstance]],
    household: Household,
) -> int:
    count = 0
    for completion, _, _ in day_completions:
        local_time = completion_local_datetime(completion.completed_at, household).time()
        if datetime.time(12, 0) <= local_time < datetime.time(14, 0):
            count += 1
    return count


def _max_consecutive_days(dates: set[datetime.date]) -> int:
    if not dates:
        return 0

    sorted_dates = sorted(dates)
    best = 1
    current = 1
    for index in range(1, len(sorted_dates)):
        if sorted_dates[index] - sorted_dates[index - 1] == datetime.timedelta(days=1):
            current += 1
            best = max(best, current)
        else:
            current = 1
    return best


def _streak_at_date(dates: set[datetime.date], on_date: datetime.date) -> int:
    if on_date not in dates:
        return 0

    streak = 1
    cursor = on_date - datetime.timedelta(days=1)
    while cursor in dates:
        streak += 1
        cursor -= datetime.timedelta(days=1)
    return streak


def _comeback_kid_achieved(
    db: Session, user: User, household: Household, local_date: datetime.date
) -> bool:
    required_dates = get_required_completion_dates(db, user, household)
    if local_date not in required_dates:
        return False

    prior_dates = {day for day in required_dates if day < local_date}
    if not prior_dates:
        return False

    last_date = max(prior_dates)
    if (local_date - last_date).days <= 1:
        return False

    return _streak_at_date(prior_dates, last_date) >= 2


def _room_master_achieved(
    db: Session,
    household: Household,
    room: Room,
    completions: list[tuple[Completion, Task, TaskInstance]],
) -> bool:
    room_tasks = db.scalars(
        select(Task).where(
            Task.household_id == household.id,
            Task.room == room,
        )
    ).all()
    if not room_tasks:
        return False

    task_counts: Counter[int] = Counter()
    for _, task, _ in completions:
        if task.room == room:
            task_counts[task.id] += 1

    return all(task_counts.get(task.id, 0) >= 10 for task in room_tasks)


def _laundry_completions_in_week(
    completions: list[tuple[Completion, Task, TaskInstance]],
    household: Household,
    week_start: datetime.date,
    week_end: datetime.date,
) -> int:
    return sum(
        1
        for row in _completions_in_range(completions, household, week_start, week_end)
        if row[1].category.name == "Laundry"
    )


def _both_members_completed_on_date(
    db: Session, household: Household, day: datetime.date
) -> bool:
    members = db.scalars(
        select(User).where(User.household_id == household.id)
    ).all()
    if len(members) < 2:
        return False

    for member in members:
        member_dates = {
            completion_local_date(row.completed_at, household)
            for row in db.scalars(
                select(Completion)
                .join(TaskInstance, Completion.task_instance_id == TaskInstance.id)
                .join(Task, TaskInstance.task_id == Task.id)
                .where(
                    Completion.user_id == member.id,
                    Completion.is_undone.is_(False),
                    Task.household_id == household.id,
                )
            ).all()
        }
        if day not in member_dates:
            return False

    return True


def _double_trouble_achieved(
    db: Session, household: Household, local_date: datetime.date
) -> bool:
    for offset in range(7):
        day = local_date - datetime.timedelta(days=offset)
        if not _both_members_completed_on_date(db, household, day):
            return False
    return True


def _helping_hand_achieved(
    db: Session, user: User, household: Household, completion: Completion
) -> bool:
    partners = db.scalars(
        select(User).where(
            User.household_id == household.id,
            User.id != user.id,
        )
    ).all()
    if not partners:
        return False

    completion_time = completion.completed_at
    if completion_time.tzinfo is None:
        completion_time = completion_time.replace(tzinfo=datetime.timezone.utc)

    window_start = completion_time - datetime.timedelta(minutes=10)
    window_end = completion_time + datetime.timedelta(minutes=10)

    for partner in partners:
        partner_completion = db.scalar(
            select(Completion)
            .join(TaskInstance, Completion.task_instance_id == TaskInstance.id)
            .join(Task, TaskInstance.task_id == Task.id)
            .where(
                Completion.user_id == partner.id,
                Completion.is_undone.is_(False),
                Task.household_id == household.id,
                Completion.completed_at >= window_start,
                Completion.completed_at <= window_end,
            )
        )
        if partner_completion is not None:
            return True
    return False


def _has_perfect_week(
    db: Session,
    user: User,
    household: Household,
    all_completions: list[tuple[Completion, Task, TaskInstance]],
) -> bool:
    today = household_today(household)
    week_start = _week_start(today)
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
        day_ids = {
            row[2].id for row in _completions_on_date(all_completions, household, day)
        }
        if not all(instance.id in day_ids for _, instance in required_due):
            return False

    return had_required


def _earned_badge_names(db: Session, user_id: int) -> set[str]:
    rows = db.scalars(
        select(Badge.name)
        .join(UserBadge, UserBadge.badge_id == Badge.id)
        .where(UserBadge.user_id == user_id)
    ).all()
    return set(rows)


def _completionist_achieved(
    db: Session, user_id: int, pending_awards: set[str]
) -> bool:
    earned = _earned_badge_names(db, user_id) | pending_awards
    return VISIBLE_BADGE_NAMES.issubset(earned)


def check_and_award_badges(
    db: Session, user: User, household: Household, completion: Completion
) -> list[str]:
    ensure_badge_definitions(db, commit=False)
    awarded: list[str] = []

    completion = db.scalar(
        select(Completion)
        .where(Completion.id == completion.id)
        .options(
            joinedload(Completion.task_instance)
            .joinedload(TaskInstance.task)
            .joinedload(Task.category)
        )
    )
    if completion is None:
        return awarded

    task = completion.task_instance.task
    local_date = completion_local_date(completion.completed_at, household)
    local_time = completion_local_datetime(completion.completed_at, household).time()
    all_completions = _load_user_completions(db, user, household)
    day_completions = _completions_on_date(all_completions, household, local_date)
    completed_instance_ids = _completed_instance_ids(day_completions)
    week_start = _week_start(local_date)
    week_end = week_start + datetime.timedelta(days=6)
    week_completions = _completions_in_range(
        all_completions, household, week_start, week_end
    )
    week_completed_ids = _completed_instance_ids(week_completions)
    month_start = local_date.replace(day=1)
    month_end = _month_end(local_date)
    month_completions = _completions_in_range(
        all_completions, household, month_start, month_end
    )
    month_completed_ids = _completed_instance_ids(month_completions)
    completion_dates = {
        completion_local_date(row[0].completed_at, household) for row in all_completions
    }

    def award(name: str) -> None:
        if _award_badge(db, user.id, name):
            awarded.append(name)

    total_tasks = len(all_completions)
    if total_tasks >= 1:
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
        if weekly_score >= goal.points_target * 2:
            award("Overachiever II")

    if local_time < datetime.time(8, 0):
        award("Early Bird")
    if local_time < datetime.time(7, 0):
        award("Rise and Shine")

    if _lunchtime_count_on_date(day_completions, household) >= 3:
        award("Lunchtime Hero")

    if _frequency_period_sweep(
        db,
        household,
        TaskFrequency.DAILY,
        local_date,
        local_date,
        completed_instance_ids,
    ):
        award("Daily Devotion")

    if _frequency_period_sweep(
        db,
        household,
        TaskFrequency.WEEKLY,
        week_start,
        week_end,
        week_completed_ids,
    ):
        award("Weekly Warrior")

    if _frequency_period_sweep(
        db,
        household,
        TaskFrequency.MONTHLY,
        month_start,
        month_end,
        month_completed_ids,
    ):
        award("Monthly Marvel")

    lifetime_score = build_score_breakdown(db, user, household)["lifetime"]["total"]
    for badge_name, threshold in LIFETIME_POINT_MILESTONES:
        if lifetime_score >= threshold:
            award(badge_name)

    for badge_name, threshold in LIFETIME_TASK_MILESTONES:
        if total_tasks >= threshold:
            award(badge_name)

    if _comeback_kid_achieved(db, user, household, local_date):
        award("Comeback Kid")

    if _helping_hand_achieved(db, user, household, completion):
        award("Helping Hand")

    if _room_master_achieved(db, household, Room.KITCHEN, all_completions):
        award("Room Master: Kitchen")
    if _room_master_achieved(db, household, Room.BATHROOM, all_completions):
        award("Room Master: Bathroom")

    if _category_week_sweep(
        db, household, "Tidying", week_start, week_end, week_completed_ids
    ):
        award("Tidy Tyrant")
    if _category_week_sweep(
        db, household, "Cooking", week_start, week_end, week_completed_ids
    ):
        award("Chef's Kiss")

    if _laundry_completions_in_week(all_completions, household, week_start, week_end) >= 5:
        award("Laundry Legend")

    if _max_consecutive_days(completion_dates) >= 30:
        award("Consistent")

    if _double_trouble_achieved(db, household, local_date):
        award("Double Trouble")

    challenge_ids = get_challenge_task_ids(db, household.id, local_date)
    challenge_completions_today = sum(
        1 for _, challenge_task, _ in day_completions if challenge_task.id in challenge_ids
    )
    if challenge_completions_today >= 3:
        award("Hat Trick Hero")

    if local_time >= datetime.time(23, 0):
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

    if datetime.time(2, 0) <= local_time < datetime.time(4, 0):
        award("Insomniac")

    if local_date.month == 1 and local_date.day == 1:
        award("New Year New Me")

    anniversary = completion_local_datetime(user.created_at, household).date()
    if local_date.month == anniversary.month and local_date.day == anniversary.day:
        award("Birthday Chores")

    if _completionist_achieved(db, user.id, set(awarded)):
        award("The Completionist")

    if awarded:
        db.flush()

    return awarded
