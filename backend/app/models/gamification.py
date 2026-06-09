import datetime
import enum
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.household import Household
    from app.models.task import Task
    from app.models.user import User


class PeriodType(enum.Enum):
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    LIFETIME = "lifetime"


class Badge(Base):
    __tablename__ = "badges"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)
    icon: Mapped[str] = mapped_column(String(63))
    is_secret: Mapped[bool] = mapped_column(Boolean, default=False)

    user_badges: Mapped[list["UserBadge"]] = relationship(back_populates="badge")


class UserBadge(Base):
    __tablename__ = "user_badges"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    badge_id: Mapped[int] = mapped_column(ForeignKey("badges.id"))
    awarded_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="badges")
    badge: Mapped["Badge"] = relationship(back_populates="user_badges")


class Leaderboard(Base):
    __tablename__ = "leaderboards"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    period_type: Mapped[PeriodType] = mapped_column(
        Enum(PeriodType, name="period_type", values_callable=lambda x: [e.value for e in x])
    )
    period_start: Mapped[datetime.date] = mapped_column(Date)
    score: Mapped[int] = mapped_column(Integer)
    snapshot_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="leaderboard_entries")


class DailyChallenge(Base):
    __tablename__ = "daily_challenges"
    __table_args__ = (
        UniqueConstraint("household_id", "challenge_date", "task_id", name="uq_daily_challenge"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    household_id: Mapped[int] = mapped_column(ForeignKey("households.id"))
    challenge_date: Mapped[datetime.date] = mapped_column(Date)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id"))

    household: Mapped["Household"] = relationship(back_populates="daily_challenges")
    task: Mapped["Task"] = relationship(back_populates="daily_challenges")


class WeeklyGoal(Base):
    __tablename__ = "weekly_goals"

    id: Mapped[int] = mapped_column(primary_key=True)
    household_id: Mapped[int] = mapped_column(ForeignKey("households.id"), unique=True)
    points_target: Mapped[int] = mapped_column(Integer)
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    household: Mapped["Household"] = relationship(back_populates="weekly_goal")
