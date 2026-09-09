"""Enforce person and video references without deleting existing data."""

from collections.abc import Sequence
from typing import Any

import sqlalchemy as sa

from alembic import op


revision: str = "e8b7c6d5a401"

down_revision: str | Sequence[str] | None = "c610a1547bed"

branch_labels: str | Sequence[str] | None = None

depends_on: str | Sequence[str] | None = None


# Neue Referenzen, die durch diese Migration eingeführt werden.
REFERENCES = (
    ("check_in", "person_id", "person", "id"),
    ("workout", "person_id", "person", "id"),
    ("workout", "video_id", "workout_video", "id"),
    # Diese Referenz existiert bereits vor dieser Migration.
    # Wir prüfen sie trotzdem, weil wir workout_phase während des
    # SQLite-Umbaus vorübergehend neu aufbauen müssen.
    ("workout_phase", "workout_id", "workout", "id"),
)


# SQLite erlaubt namenlose Foreign Keys.
#
# Um einen solchen Foreign Key mit Alembics Batch-Modus entfernen zu können,
# geben wir ihm während der Reflection vorübergehend einen deterministischen
# Namen.
NAMING_CONVENTION = {
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
}

UNNAMED_WORKOUT_PHASE_FK_NAME = "fk_workout_phase_workout_id_workout"


def _check_orphans() -> None:
    """Abort before schema changes if broken references already exist."""

    connection = op.get_bind()
    problems: list[str] = []

    for table, column, parent, parent_column in REFERENCES:
        rows = connection.execute(
            sa.text(
                f"SELECT child.id, child.{column} "
                f"FROM {table} AS child "
                f"LEFT JOIN {parent} AS parent "
                f"ON child.{column} = parent.{parent_column} "
                f"WHERE parent.{parent_column} IS NULL "
                f"ORDER BY child.id "
                f"LIMIT 10"
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


def _find_workout_phase_foreign_key() -> dict[str, Any]:
    """Find the existing workout_phase.workout_id -> workout.id FK."""

    inspector = sa.inspect(op.get_bind())

    matches = [
        foreign_key
        for foreign_key in inspector.get_foreign_keys("workout_phase")
        if foreign_key.get("constrained_columns") == ["workout_id"]
        and foreign_key.get("referred_table") == "workout"
        and foreign_key.get("referred_columns") == ["id"]
    ]

    if len(matches) != 1:
        raise RuntimeError(
            "Erwartet wurde genau ein Foreign Key "
            "workout_phase.workout_id -> workout.id, "
            f"gefunden wurden aber {len(matches)}."
        )

    return matches[0]


def _detach_workout_phase_foreign_key() -> tuple[str, dict[str, Any]]:
    """Temporarily remove the FK that prevents SQLite from rebuilding workout.

    SQLite implements many ALTER TABLE operations by creating a replacement
    table, copying the data, dropping the old table and renaming the
    replacement.

    workout_phase already references workout. With foreign_keys=ON SQLite
    therefore correctly refuses Alembic's DROP TABLE workout.

    We solve that without disabling FK enforcement:
    1. rebuild workout_phase without its FK,
    2. rebuild workout,
    3. restore the workout_phase FK.
    """

    foreign_key = _find_workout_phase_foreign_key()

    original_name = foreign_key.get("name")
    options = dict(foreign_key.get("options") or {})

    if original_name is None:
        # Alembic cannot directly drop an unnamed SQLite FK.
        # The naming convention gives the reflected constraint a temporary,
        # deterministic name.
        constraint_name = UNNAMED_WORKOUT_PHASE_FK_NAME

        with op.batch_alter_table(
            "workout_phase",
            naming_convention=NAMING_CONVENTION,
        ) as batch:
            batch.drop_constraint(
                constraint_name,
                type_="foreignkey",
            )
    else:
        constraint_name = str(original_name)

        with op.batch_alter_table("workout_phase") as batch:
            batch.drop_constraint(
                constraint_name,
                type_="foreignkey",
            )

    return constraint_name, options


def _restore_workout_phase_foreign_key(
    constraint_name: str,
    options: dict[str, Any],
) -> None:
    """Restore workout_phase.workout_id -> workout.id."""

    with op.batch_alter_table("workout_phase") as batch:
        batch.create_foreign_key(
            constraint_name,
            "workout",
            ["workout_id"],
            ["id"],
            ondelete=options.get("ondelete"),
            onupdate=options.get("onupdate"),
        )


def _upgrade_workout() -> None:
    """Add the new workout FKs while preserving workout_phase references."""

    constraint_name, options = _detach_workout_phase_foreign_key()

    with op.batch_alter_table("workout") as batch:
        batch.create_foreign_key(
            "fk_workout_person",
            "person",
            ["person_id"],
            ["id"],
            ondelete="RESTRICT",
        )

        batch.create_foreign_key(
            "fk_workout_video",
            "workout_video",
            ["video_id"],
            ["id"],
            ondelete="RESTRICT",
        )

    _restore_workout_phase_foreign_key(
        constraint_name,
        options,
    )


def _downgrade_workout() -> None:
    """Remove the new workout FKs while preserving workout_phase references."""

    constraint_name, options = _detach_workout_phase_foreign_key()

    with op.batch_alter_table("workout") as batch:
        batch.drop_constraint(
            "fk_workout_video",
            type_="foreignkey",
        )

        batch.drop_constraint(
            "fk_workout_person",
            type_="foreignkey",
        )

    _restore_workout_phase_foreign_key(
        constraint_name,
        options,
    )


def upgrade() -> None:
    _check_orphans()

    with op.batch_alter_table("check_in") as batch:
        batch.create_foreign_key(
            "fk_check_in_person",
            "person",
            ["person_id"],
            ["id"],
            ondelete="RESTRICT",
        )

    _upgrade_workout()


def downgrade() -> None:
    _downgrade_workout()

    with op.batch_alter_table("check_in") as batch:
        batch.drop_constraint(
            "fk_check_in_person",
            type_="foreignkey",
        )