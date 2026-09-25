"""Freeze workout expectation for descriptive post-workout comparison.

Revision ID: c3a91e202609
Revises: a6d9f2c4e810
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "c3a91e202609"
down_revision: str | Sequence[str] | None = "a6d9f2c4e810"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("workout", sa.Column("expectation", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("workout", "expectation")
