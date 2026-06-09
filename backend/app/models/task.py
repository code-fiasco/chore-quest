import datetime
import enum
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.household import Category, Household
    from app.models.user import User


class TaskFrequency(enum.Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class Room(enum.Enum):
    KITCHEN = "Kitchen"
    BATHROOM = "Bathroom"
    BEDROOM = "Bedroom"
    LIVING_ROOM = "Living Room"
    DINING_ROOM = "Dining Room"
    HALLWAY = "Hallway"
    OTHER = "Other"


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text)
    frequency: Mapped[TaskFrequency] = mapped_column(
        Enum(TaskFrequency, name="task_frequency", values_callable=lambda x: [e.value for e in x])
    )
    base_points: Mapped[int] = mapped_column(Integer, default=10)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"))
    room: Mapped[Room] = mapped_column(
        Enum(Room, name="room", values_callable=lambda x: [e.value for e in x])
    )
    is_required: Mapped[bool] = mapped_column(Boolean, default=True)
    household_id: Mapped[int] = mapped_column(ForeignKey("households.id"))
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    category: Mapped["Category"] = relationship(back_populates="tasks")
    household: Mapped["Household"] = relationship(back_populates="tasks")
    instances: Mapped[list["TaskInstance"]] = relationship(back_populates="task")


class TaskInstance(Base):
    __tablename__ = "task_instances"

    id: Mapped[int] = mapped_column(primary_key=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id"))
    period_start: Mapped[datetime.date] = mapped_column(Date)
    period_end: Mapped[datetime.date] = mapped_column(Date)
    completed_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    completed_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True))
    is_locked: Mapped[bool] = mapped_column(Boolean, default=False)

    task: Mapped["Task"] = relationship(back_populates="instances")
    completed_by: Mapped[Optional["User"]] = relationship(back_populates="completed_instances")
    completions: Mapped[list["Completion"]] = relationship(back_populates="task_instance")


class Completion(Base):
    """Immutable completion history. Rows must never be deleted (PRD §23)."""

    __tablename__ = "completions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    task_instance_id: Mapped[int] = mapped_column(ForeignKey("task_instances.id"))
    points_awarded: Mapped[int] = mapped_column(Integer)
    completed_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True))
    is_undone: Mapped[bool] = mapped_column(Boolean, default=False)

    user: Mapped["User"] = relationship(back_populates="completions")
    task_instance: Mapped["TaskInstance"] = relationship(back_populates="completions")
