"""add workout heart rate summary

Revision ID: d2a4f6b8c301
Revises: b5e7c9d3a102
Create Date: 2026-09-23
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "d2a4f6b8c301"
down_revision: str | Sequence[str] | None = "b5e7c9d3a102"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("workout", sa.Column("heart_rate_sample_count", sa.Integer(), nullable=True))
    op.add_column("workout", sa.Column("heart_rate_average_bpm", sa.Integer(), nullable=True))
    op.add_column("workout", sa.Column("heart_rate_max_bpm", sa.Integer(), nullable=True))
    op.add_column(
        "workout",
        sa.Column("heart_rate_below_target_percent", sa.Integer(), nullable=True),
    )
    op.add_column(
        "workout",
        sa.Column("heart_rate_in_target_percent", sa.Integer(), nullable=True),
    )
    op.add_column(
        "workout",
        sa.Column("heart_rate_above_target_percent", sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("workout", "heart_rate_above_target_percent")
    op.drop_column("workout", "heart_rate_in_target_percent")
    op.drop_column("workout", "heart_rate_below_target_percent")
    op.drop_column("workout", "heart_rate_max_bpm")
    op.drop_column("workout", "heart_rate_average_bpm")
    op.drop_column("workout", "heart_rate_sample_count")
