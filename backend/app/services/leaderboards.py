import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.gamification import Leaderboard, PeriodType, WeeklyGoal
from app.models.household import Household
from app.models.user import User
from app.services.scoring import _DueTasksCache, build_score_breakdown
from app.services.challenges import (
    MAX_DAILY_CHALLENGE_COUNT,
    MIN_DAILY_CHALLENGE_COUNT,
    clear_daily_challenges_for_date,
)
from app.services.tasks import household_today


class GoalError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


def _week_start(day: datetime.date) -> datetime.date:
    return day - datetime.timedelta(days=day.weekday())


def _month_start(day: datetime.date) -> datetime.date:
    return day.replace(day=1)


def _rank_members(members: list[User], scores: dict[int, int]) -> list[dict]:
    ranked = sorted(
        members,
        key=lambda member: (-scores.get(member.id, 0), member.display_name.lower()),
    )
    result = []
    for index, member in enumerate(ranked, start=1):
        result.append(
            {
                "rank": index,
                "user_id": member.id,
                "display_name": member.display_name,
                "avatar": member.avatar,
                "score": scores.get(member.id, 0),
            }
        )
    return result


def get_leaderboards(db: Session, user: User) -> dict:
    household = db.get(Household, user.household_id)
    if household is None:
        return {"weekly": [], "monthly": [], "lifetime": []}

    members = list(
        db.scalars(select(User).where(User.household_id == household.id)).all()
    )

    weekly_scores: dict[int, int] = {}
    monthly_scores: dict[int, int] = {}
    lifetime_scores: dict[int, int] = {}
    due_cache = _DueTasksCache(db, household)

    for member in members:
        breakdown = build_score_breakdown(
            db, member, household, due_cache=due_cache
        )
        weekly_scores[member.id] = breakdown["weekly"]["total"]
        monthly_scores[member.id] = breakdown["monthly"]["total"]
        lifetime_scores[member.id] = breakdown["lifetime"]["total"]

    return {
        "weekly": _rank_members(members, weekly_scores),
        "monthly": _rank_members(members, monthly_scores),
        "lifetime": _rank_members(members, lifetime_scores),
    }


def snapshot_leaderboards(db: Session, household_id: int) -> None:
    household = db.get(Household, household_id)
    if household is None:
        return

    members = list(
        db.scalars(select(User).where(User.household_id == household_id)).all()
    )
    today = household_today(household)
    week_start = _week_start(today)
    month_start = _month_start(today)
    lifetime_start = datetime.date(2000, 1, 1)
    now = datetime.datetime.now(datetime.timezone.utc)

    for member in members:
        breakdown = build_score_breakdown(db, member, household)
        snapshots = [
            (PeriodType.WEEKLY, week_start, breakdown["weekly"]["total"]),
            (PeriodType.MONTHLY, month_start, breakdown["monthly"]["total"]),
            (PeriodType.LIFETIME, lifetime_start, breakdown["lifetime"]["total"]),
        ]
        for period_type, period_start, score in snapshots:
            db.add(
                Leaderboard(
                    user_id=member.id,
                    period_type=period_type,
                    period_start=period_start,
                    score=score,
                    snapshot_at=now,
                )
            )

    db.commit()


def get_weekly_goal(db: Session, user: User) -> dict:
    household = db.get(Household, user.household_id)
    if household is None:
        raise GoalError("Household not found", status_code=404)

    goal = db.scalar(select(WeeklyGoal).where(WeeklyGoal.household_id == household.id))
    members = list(
        db.scalars(select(User).where(User.household_id == household.id)).all()
    )

    progress = []
    for member in members:
        weekly_score = build_score_breakdown(db, member, household)["weekly"]["total"]
        progress.append(
            {
                "user_id": member.id,
                "display_name": member.display_name,
                "avatar": member.avatar,
                "weekly_score": weekly_score,
            }
        )

    return {
        "points_target": goal.points_target if goal else None,
        "daily_challenges_enabled": household.daily_challenges_enabled,
        "daily_challenge_count": household.daily_challenge_count,
        "members": progress,
    }


def set_weekly_goal(
    db: Session,
    user: User,
    points_target: int | None = None,
    *,
    daily_challenges_enabled: bool | None = None,
    daily_challenge_count: int | None = None,
) -> dict:
    household = db.get(Household, user.household_id)
    if household is None:
        raise GoalError("Household not found", status_code=404)

    regenerate_today_challenges = False

    if points_target is not None:
        if points_target < 1:
            raise GoalError("Weekly goal must be at least 1 point")

        goal = db.scalar(
            select(WeeklyGoal).where(WeeklyGoal.household_id == user.household_id)
        )
        if goal is None:
            goal = WeeklyGoal(household_id=user.household_id, points_target=points_target)
            db.add(goal)
        else:
            goal.points_target = points_target

    if daily_challenges_enabled is not None:
        if daily_challenges_enabled and not household.daily_challenges_enabled:
            regenerate_today_challenges = True
        household.daily_challenges_enabled = daily_challenges_enabled

    if daily_challenge_count is not None:
        if not MIN_DAILY_CHALLENGE_COUNT <= daily_challenge_count <= MAX_DAILY_CHALLENGE_COUNT:
            raise GoalError(
                f"Daily challenge count must be between "
                f"{MIN_DAILY_CHALLENGE_COUNT} and {MAX_DAILY_CHALLENGE_COUNT}"
            )
        if daily_challenge_count != household.daily_challenge_count:
            regenerate_today_challenges = True
        household.daily_challenge_count = daily_challenge_count

    if regenerate_today_challenges and household.daily_challenges_enabled:
        clear_daily_challenges_for_date(
            db, household.id, household_today(household)
        )

    db.commit()
    return get_weekly_goal(db, user)
