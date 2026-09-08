"""add check in health data

Revision ID: c610a1547bed
Revises: 39c325d1bd7e
Create Date: 2026-09-08 15:46:13.189327

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c610a1547bed"
down_revision: str | Sequence[str] | None = "39c325d1bd7e"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "check_in",
        sa.Column("current_weight_kg", sa.Float(), nullable=True),
    )
    op.add_column(
        "check_in",
        sa.Column("sleep_hours", sa.Float(), nullable=True),
    )
    op.add_column(
        "check_in",
        sa.Column("steps", sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("check_in", "steps")
    op.drop_column("check_in", "sleep_hours")
    op.drop_column("check_in", "current_weight_kg")
