"""add workout distance

Revision ID: 0d6027eb0de0
Revises: ad3306bf474c
Create Date: 2026-09-06 12:57:52.922654

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy import inspect

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0d6027eb0de0"
down_revision: str | Sequence[str] | None = "ad3306bf474c"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """
    Fügt die workout-relative Distanz hinzu.

    Die Migration ist absichtlich robust gegen einen bereits
    teilweise ausgeführten SQLite-Lauf:

    - existiert distance_m noch nicht, wird die Spalte angelegt
    - existiert sie bereits, wird sie nicht erneut angelegt

    Der Default 0 bleibt auf SQLite bewusst bestehen. Er ist
    unkritisch und sorgt zusätzlich dafür, dass ältere Inserts
    ohne distance_m nicht fehlschlagen.
    """

    connection = op.get_bind()
    inspector = inspect(connection)

    column_names = {column["name"] for column in inspector.get_columns("workout")}

    if "distance_m" not in column_names:
        op.add_column(
            "workout",
            sa.Column(
                "distance_m",
                sa.Integer(),
                nullable=False,
                server_default="0",
            ),
        )


def downgrade() -> None:
    connection = op.get_bind()
    inspector = inspect(connection)

    column_names = {column["name"] for column in inspector.get_columns("workout")}

    if "distance_m" in column_names:
        op.drop_column(
            "workout",
            "distance_m",
        )
