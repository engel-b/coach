"""Enforce person and video references without deleting existing data."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "e8b7c6d5a401"
down_revision: str | Sequence[str] | None = "c610a1547bed"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

REFERENCES = (
    ("check_in", "person_id", "person", "id", "fk_check_in_person"),
    ("workout", "person_id", "person", "id", "fk_workout_person"),
    ("workout", "video_id", "workout_video", "id", "fk_workout_video"),
)


def _check_orphans() -> None:
    connection = op.get_bind()
    problems: list[str] = []
    for table, column, parent, parent_column, _ in REFERENCES:
        rows = connection.execute(
            sa.text(
                f"SELECT child.id, child.{column} FROM {table} AS child "
                f"LEFT JOIN {parent} AS parent "
                f"ON child.{column} = parent.{parent_column} "
                f"WHERE parent.{parent_column} IS NULL "
                f"ORDER BY child.id LIMIT 10"
            )
        ).all()
        if rows:
            problems.append(f"{table}.{column}: {rows!r}")
    if problems:
        raise RuntimeError(
            "Migration abgebrochen: verwaiste Referenzen gefunden. "
            "Bitte zuerst die Bestandsprüfung ausführen und die Daten "
            "bewusst korrigieren. Es wurden keine Datensätze gelöscht. "
            + "; ".join(problems)
        )


def upgrade() -> None:
    _check_orphans()
    with op.batch_alter_table("check_in") as batch:
        batch.create_foreign_key(
            "fk_check_in_person", "person", ["person_id"], ["id"], ondelete="RESTRICT"
        )
    with op.batch_alter_table("workout") as batch:
        batch.create_foreign_key(
            "fk_workout_person", "person", ["person_id"], ["id"], ondelete="RESTRICT"
        )
        batch.create_foreign_key(
            "fk_workout_video", "workout_video", ["video_id"], ["id"], ondelete="RESTRICT"
        )


def downgrade() -> None:
    with op.batch_alter_table("workout") as batch:
        batch.drop_constraint("fk_workout_video", type_="foreignkey")
        batch.drop_constraint("fk_workout_person", type_="foreignkey")
    with op.batch_alter_table("check_in") as batch:
        batch.drop_constraint("fk_check_in_person", type_="foreignkey")
