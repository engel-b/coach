"""add resting heart rate to check in

Revision ID: b5e7c9d3a102
Revises: 8f3f4a1c2d77
Create Date: 2026-09-23
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "b5e7c9d3a102"
down_revision: str | Sequence[str] | None = "8f3f4a1c2d77"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "check_in",
        sa.Column("resting_heart_rate_bpm", sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("check_in", "resting_heart_rate_bpm")
