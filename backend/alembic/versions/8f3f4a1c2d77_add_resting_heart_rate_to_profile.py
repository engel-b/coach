"""add resting heart rate to person profile

Revision ID: 8f3f4a1c2d77
Revises: e8b7c6d5a401
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "8f3f4a1c2d77"
down_revision: str | Sequence[str] | None = "e8b7c6d5a401"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "person_profile",
        sa.Column("resting_heart_rate_bpm", sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("person_profile", "resting_heart_rate_bpm")
