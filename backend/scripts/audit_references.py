"""Read-only referential-integrity report for a chosen SQLite database."""

import argparse
from pathlib import Path
import sqlite3


REFERENCES = (
    # child table, child PK, FK column, parent table, parent PK
    ("check_in", "id", "person_id", "person", "id"),
    ("workout", "id", "person_id", "person", "id"),
    ("workout", "id", "video_id", "workout_video", "id"),
    ("person_profile", "person_id", "person_id", "person", "id"),
    ("workout_phase", "id", "workout_id", "workout", "id"),
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__,
    )
    parser.add_argument(
        "database",
        type=Path,
        help="Existing SQLite database file",
    )

    args = parser.parse_args()
    path = args.database.resolve()

    if not path.is_file():
        parser.error(f"Database does not exist: {path}")

    # mode=ro verhindert, dass das Skript die Datenbank verändert
    # oder versehentlich eine neue Datei erzeugt.
    with sqlite3.connect(
        path.as_uri() + "?mode=ro",
        uri=True,
    ) as connection:
        connection.row_factory = sqlite3.Row

        for (
            table,
            child_pk,
            column,
            parent,
            parent_column,
        ) in REFERENCES:
            rows = connection.execute(
                f"""
                SELECT
                    child.{child_pk} AS child_id,
                    child.{column} AS reference_value
                FROM {table} AS child
                LEFT JOIN {parent} AS parent
                    ON child.{column} = parent.{parent_column}
                WHERE parent.{parent_column} IS NULL
                ORDER BY child.{child_pk}
                """
            ).fetchall()

            print(
                f"\n{table}.{column} -> "
                f"{parent}.{parent_column}: "
                f"{len(rows)} orphan(s)"
            )

            for row in rows:
                print(
                    f"  {child_pk}={row['child_id']!r}, "
                    f"{column}={row['reference_value']!r}"
                )

        violations = connection.execute(
            "PRAGMA foreign_key_check"
        ).fetchall()

        print(
            f"\nExisting foreign-key violations: "
            f"{len(violations)}"
        )

        for row in violations:
            print(tuple(row))


if __name__ == "__main__":
    main()