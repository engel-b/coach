"""add workout type

Revision ID: f4c2a9e78110
Revises: d2a4f6b8c301
Create Date: 2026-09-23
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "f4c2a9e78110"
down_revision: str | Sequence[str] | None = "d2a4f6b8c301"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("workout", sa.Column("workout_type", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("workout", "workout_type")
