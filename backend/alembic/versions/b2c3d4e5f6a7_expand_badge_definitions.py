"""expand badge definitions

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-06-11 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
from sqlalchemy.orm import Session

from app.services.badges import ensure_badge_definitions

revision: str = "b2c3d4e5f6a7"
down_revision: Union[str, None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    session = Session(bind=bind)
    try:
        ensure_badge_definitions(session, commit=False)
        session.commit()
    finally:
        session.close()


def downgrade() -> None:
    pass
