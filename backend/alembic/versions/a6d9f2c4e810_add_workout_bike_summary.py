"""add workout bike summary

Revision ID: a6d9f2c4e810
Revises: f4c2a9e78110
Create Date: 2026-09-23
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "a6d9f2c4e810"
down_revision: str | Sequence[str] | None = "f4c2a9e78110"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("workout", sa.Column("bike_power_sample_count", sa.Integer(), nullable=True))
    op.add_column("workout", sa.Column("bike_average_power_w", sa.Integer(), nullable=True))
    op.add_column("workout", sa.Column("bike_cadence_sample_count", sa.Integer(), nullable=True))
    op.add_column("workout", sa.Column("bike_average_cadence_rpm", sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column("workout", "bike_average_cadence_rpm")
    op.drop_column("workout", "bike_cadence_sample_count")
    op.drop_column("workout", "bike_average_power_w")
    op.drop_column("workout", "bike_power_sample_count")
