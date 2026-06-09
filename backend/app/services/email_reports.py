import datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.gamification import UserBadge
from app.models.household import Household
from app.models.task import Completion, Task, TaskInstance
from app.models.user import User
from app.services.challenges import ensure_today_challenge_ids, generate_daily_challenges
from app.services.email import send_email
from app.services.scoring import build_score_breakdown
from app.services.streaks import calculate_current_streak, completion_local_date
from app.services.tasks import household_today

TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates" / "email"
_jinja = Environment(
    loader=FileSystemLoader(TEMPLATE_DIR),
    autoescape=select_autoescape(["html", "xml"]),
)


def _week_start(day: datetime.date) -> datetime.date:
    return day - datetime.timedelta(days=day.weekday())


def _last_week_bounds(today: datetime.date) -> tuple[datetime.date, datetime.date]:
    last_sunday = today - datetime.timedelta(days=1)
    last_monday = last_sunday - datetime.timedelta(days=6)
    return last_monday, last_sunday


def _member_completions_on_date(
    db: Session, user: User, household: Household, day: datetime.date
) -> list[str]:
    completions = db.scalars(
        select(Completion)
        .join(TaskInstance, Completion.task_instance_id == TaskInstance.id)
        .join(Task, TaskInstance.task_id == Task.id)
        .where(
            Completion.user_id == user.id,
            Completion.is_undone.is_(False),
            Task.household_id == household.id,
        )
        .options(joinedload(Completion.task_instance).joinedload(TaskInstance.task))
    ).all()

    names = []
    for completion in completions:
        if completion_local_date(completion.completed_at, household) == day:
            names.append(completion.task_instance.task.name)
    return names


def _build_daily_context(db: Session, household: Household) -> dict:
    today = household_today(household)
    members = list(
        db.scalars(select(User).where(User.household_id == household.id)).all()
    )

    member_rows = []
    for member in members:
        breakdown = build_score_breakdown(db, member, household, as_of=today)
        member_rows.append(
            {
                "display_name": member.display_name,
                "avatar": member.avatar,
                "daily_score": breakdown["daily"]["total"],
                "tasks_completed": _member_completions_on_date(
                    db, member, household, today
                ),
                "streak": calculate_current_streak(db, member, household),
            }
        )

    winner = max(member_rows, key=lambda row: row["daily_score"]) if member_rows else None
    if winner and winner["daily_score"] == 0:
        winner = None

    return {
        "household_name": household.name,
        "date_label": today.strftime("%A, %d %B %Y"),
        "members": member_rows,
        "winner": winner,
        "frontend_url": _frontend_url(),
    }


def _build_weekly_context(db: Session, household: Household) -> dict:
    today = household_today(household)
    week_start, week_end = _last_week_bounds(today)

    members = list(
        db.scalars(select(User).where(User.household_id == household.id)).all()
    )

    member_rows = []
    for member in members:
        breakdown = build_score_breakdown(db, member, household, as_of=week_end)
        member_rows.append(
            {
                "display_name": member.display_name,
                "avatar": member.avatar,
                "weekly_score": breakdown["weekly"]["total"],
                "streak": calculate_current_streak(db, member, household),
            }
        )

    winner = max(member_rows, key=lambda row: row["weekly_score"]) if member_rows else None
    if winner and winner["weekly_score"] == 0:
        winner = None

    week_badges = []
    for member in members:
        rows = db.scalars(
            select(UserBadge)
            .where(UserBadge.user_id == member.id)
            .options(joinedload(UserBadge.badge))
        ).all()
        for row in rows:
            awarded_local = completion_local_date(row.awarded_at, household)
            if week_start <= awarded_local <= week_end:
                week_badges.append(
                    {
                        "display_name": member.display_name,
                        "badge_name": row.badge.name,
                        "is_secret": row.badge.is_secret,
                    }
                )

    ensure_today_challenge_ids(db, household)
    challenges = generate_daily_challenges(db, household.id, today)
    challenge_tasks = []
    for challenge in challenges:
        task = db.get(Task, challenge.task_id)
        if task is not None:
            challenge_tasks.append(task.name)

    return {
        "household_name": household.name,
        "week_label": f"{week_start.strftime('%d %b')} – {week_end.strftime('%d %b %Y')}",
        "members": member_rows,
        "winner": winner,
        "badges_earned": week_badges,
        "challenge_preview": challenge_tasks,
        "frontend_url": _frontend_url(),
    }


def _frontend_url() -> str:
    from app.config import settings

    return settings.frontend_url.rstrip("/")


def _render_pair(template_base: str, context: dict) -> tuple[str, str]:
    html = _jinja.get_template(f"{template_base}.html").render(**context)
    text = _jinja.get_template(f"{template_base}.txt").render(**context)
    return html, text


def send_daily_summary(db: Session, household_id: int) -> None:
    household = db.get(Household, household_id)
    if household is None:
        return

    members = db.scalars(select(User).where(User.household_id == household_id)).all()
    if not members:
        return

    context = _build_daily_context(db, household)
    html, text = _render_pair("daily_summary", context)

    for member in members:
        send_email(
            to=member.email,
            subject="Chore Quest — Daily Summary",
            html_body=html,
            text_body=text,
        )


def send_weekly_roundup(db: Session, household_id: int) -> None:
    household = db.get(Household, household_id)
    if household is None:
        return

    members = db.scalars(select(User).where(User.household_id == household_id)).all()
    if not members:
        return

    context = _build_weekly_context(db, household)
    html, text = _render_pair("weekly_roundup", context)

    for member in members:
        send_email(
            to=member.email,
            subject="Chore Quest — Weekly Round Up",
            html_body=html,
            text_body=text,
        )
