from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from adapters.persistence.check_in_model import CheckInModel  # noqa: F401
from adapters.persistence.database import DATABASE_URL, Base
from adapters.persistence.workout_model import (  # noqa: F401
    WorkoutModel,
    WorkoutPhaseModel,
)
from adapters.persistence.workout_video_model import WorkoutVideoModel  # noqa: F401
from alembic import context

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)


# Alembic muss alle SQLAlchemy-Modelle kennen.
#
# Die Imports oben sorgen dafür, dass CheckInModel,
# WorkoutModel und WorkoutPhaseModel in Base.metadata
# registriert sind.
target_metadata = Base.metadata


# Wir übernehmen die DB-URL aus unserer Anwendung.
#
# Dadurch gibt es nur EINE Stelle, an der die
# Datenbankverbindung konfiguriert wird.
config.set_main_option(
    "sqlalchemy.url",
    DATABASE_URL,
)


def run_migrations_offline() -> None:
    """
    Migration ohne aktive DB-Verbindung.

    Wird von Alembic beispielsweise für SQL-Generierung verwendet.
    """

    url = config.get_main_option("sqlalchemy.url")

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={
            "paramstyle": "named",
        },
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Normaler Modus:
    Alembic verbindet sich mit der Datenbank und führt
    die Migrationen dort aus.
    """

    connectable = engine_from_config(
        config.get_section(
            config.config_ini_section,
            {},
        ),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
