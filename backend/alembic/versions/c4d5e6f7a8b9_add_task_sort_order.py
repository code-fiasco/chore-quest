"""add task sort_order

Revision ID: c4d5e6f7a8b9
Revises: b2c3d4e5f6a7
Create Date: 2026-06-11 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "c4d5e6f7a8b9"
down_revision: Union[str, None] = "b2c3d4e5f6a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "tasks",
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
    )
    op.alter_column("tasks", "sort_order", server_default=None)

    connection = op.get_bind()
    households = connection.execute(sa.text("SELECT id FROM households")).fetchall()
    for (household_id,) in households:
        for frequency in ("daily", "weekly", "monthly"):
            rows = connection.execute(
                sa.text(
                    """
                    SELECT id FROM tasks
                    WHERE household_id = :household_id AND frequency = :frequency
                    ORDER BY id
                    """
                ),
                {"household_id": household_id, "frequency": frequency},
            ).fetchall()
            for index, (task_id,) in enumerate(rows):
                connection.execute(
                    sa.text(
                        "UPDATE tasks SET sort_order = :sort_order WHERE id = :task_id"
                    ),
                    {"sort_order": index, "task_id": task_id},
                )


def downgrade() -> None:
    op.drop_column("tasks", "sort_order")
