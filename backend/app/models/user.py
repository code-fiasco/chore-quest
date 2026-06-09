import datetime
import enum
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.gamification import Leaderboard, UserBadge
    from app.models.household import Household
    from app.models.task import Completion, TaskInstance


class UserRole(enum.Enum):
    MEMBER = "member"
    ADMIN = "admin"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    display_name: Mapped[str] = mapped_column(String(255))
    avatar: Mapped[str] = mapped_column(String(63))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role", values_callable=lambda x: [e.value for e in x]),
        default=UserRole.MEMBER,
    )
    household_id: Mapped[int] = mapped_column(ForeignKey("households.id"))
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    household: Mapped["Household"] = relationship(back_populates="users")
    completions: Mapped[list["Completion"]] = relationship(back_populates="user")
    completed_instances: Mapped[list["TaskInstance"]] = relationship(
        back_populates="completed_by"
    )
    badges: Mapped[list["UserBadge"]] = relationship(back_populates="user")
    leaderboard_entries: Mapped[list["Leaderboard"]] = relationship(back_populates="user")
