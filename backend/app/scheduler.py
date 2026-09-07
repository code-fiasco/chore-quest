import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import select

from app.database import SessionLocal
from app.models.household import Household
from app.services.challenges import generate_daily_challenges
from app.services.email_reports import send_daily_summary, send_weekly_roundup
from app.services.leaderboards import snapshot_leaderboards

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()


def _run_daily_challenges(household_id: int) -> None:
    db = SessionLocal()
    try:
        household = db.get(Household, household_id)
        if household is None or not household.daily_challenges_enabled:
            return
        generate_daily_challenges(db, household_id)
        db.commit()
        logger.info("Generated daily challenges for household %s", household_id)
    except Exception:
        logger.exception("Failed daily challenges for household %s", household_id)
        db.rollback()
    finally:
        db.close()


def _run_daily_email(household_id: int) -> None:
    db = SessionLocal()
    try:
        send_daily_summary(db, household_id)
        logger.info("Sent daily summary email for household %s", household_id)
    except Exception:
        logger.exception("Failed daily email for household %s", household_id)
        db.rollback()
    finally:
        db.close()


def _run_weekly_email(household_id: int) -> None:
    db = SessionLocal()
    try:
        send_weekly_roundup(db, household_id)
        db.commit()
        logger.info("Sent weekly roundup email for household %s", household_id)
    except Exception:
        logger.exception("Failed weekly email for household %s", household_id)
        db.rollback()
    finally:
        db.close()


def _run_leaderboard_snapshot(household_id: int) -> None:
    db = SessionLocal()
    try:
        snapshot_leaderboards(db, household_id)
        logger.info("Saved leaderboard snapshot for household %s", household_id)
    except Exception:
        logger.exception("Failed leaderboard snapshot for household %s", household_id)
        db.rollback()
    finally:
        db.close()


def schedule_household_jobs(household: Household) -> None:
    tz = household.timezone
    hid = household.id

    scheduler.add_job(
        _run_daily_challenges,
        CronTrigger(hour=6, minute=0, timezone=tz),
        args=[hid],
        id=f"challenges_{hid}",
        replace_existing=True,
    )
    scheduler.add_job(
        _run_daily_email,
        CronTrigger(hour=22, minute=0, timezone=tz),
        args=[hid],
        id=f"daily_email_{hid}",
        replace_existing=True,
    )
    scheduler.add_job(
        _run_weekly_email,
        CronTrigger(day_of_week="mon", hour=8, minute=0, timezone=tz),
        args=[hid],
        id=f"weekly_email_{hid}",
        replace_existing=True,
    )
    scheduler.add_job(
        _run_leaderboard_snapshot,
        CronTrigger(day_of_week="mon", hour=0, minute=0, timezone=tz),
        args=[hid],
        id=f"leaderboard_{hid}",
        replace_existing=True,
    )


def refresh_all_household_schedules() -> None:
    db = SessionLocal()
    try:
        households = db.scalars(select(Household)).all()
        for household in households:
            schedule_household_jobs(household)
    finally:
        db.close()


def start_scheduler() -> None:
    if scheduler.running:
        refresh_all_household_schedules()
        return

    refresh_all_household_schedules()
    scheduler.start()
    logger.info("APScheduler started")


def shutdown_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("APScheduler stopped")
