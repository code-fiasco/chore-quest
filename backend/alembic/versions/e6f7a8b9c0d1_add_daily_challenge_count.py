"""add daily_challenge_count to households

Revision ID: e6f7a8b9c0d1
Revises: d5e6f7a8b9c0
Create Date: 2026-07-05 08:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "e6f7a8b9c0d1"
down_revision: Union[str, None] = "d5e6f7a8b9c0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "households",
        sa.Column(
            "daily_challenge_count",
            sa.Integer(),
            nullable=False,
            server_default="3",
        ),
    )
    op.alter_column("households", "daily_challenge_count", server_default=None)


def downgrade() -> None:
    op.drop_column("households", "daily_challenge_count")
