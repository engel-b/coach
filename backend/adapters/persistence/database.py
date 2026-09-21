from collections.abc import Generator
from pathlib import Path
from sqlite3 import Connection as SQLiteConnection

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

# backend/adapters/persistence/database.py
#                ↓
# backend/
#                ↓
# Coach/
PROJECT_ROOT = Path(__file__).resolve().parents[3]

DATABASE_PATH = PROJECT_ROOT / "data" / "db" / "health-coach.db"

# SQLite kann die Datenbankdatei selbst erzeugen, aber nicht das
# übergeordnete Verzeichnis. Das ist insbesondere bei einer frischen
# Installation oder auf einem CI-Runner relevant.
DATABASE_PATH.parent.mkdir(
    parents=True,
    exist_ok=True,
)

DATABASE_URL = f"sqlite:///{DATABASE_PATH}"


class Base(DeclarativeBase):
    """
    Basisklasse für alle SQLAlchemy-Tabellenmodelle.

    Java-/JPA-Vergleich:
    Die konkreten Klassen darunter entsprechen ungefähr @Entity-Klassen.
    """


def enable_sqlite_foreign_keys(engine: Engine) -> None:
    """Activate SQLite foreign keys on every DB-API connection."""
    if engine.dialect.name != "sqlite":
        return

    @event.listens_for(engine, "connect")
    def _enable(dbapi_connection: object, connection_record: object) -> None:
        if not isinstance(dbapi_connection, SQLiteConnection):
            return
        cursor = dbapi_connection.cursor()
        try:
            cursor.execute("PRAGMA foreign_keys=ON")
        finally:
            cursor.close()


def make_engine(url: str) -> Engine:
    engine = create_engine(
        url,
        connect_args={"check_same_thread": False} if url.startswith("sqlite") else {},
    )
    enable_sqlite_foreign_keys(engine)
    return engine


engine = make_engine(DATABASE_URL)

SessionFactory = sessionmaker(
    bind=engine,
    expire_on_commit=False,
)


def create_session() -> Session:
    """
    Erzeugt eine neue DB-Session.

    Java-Vergleich grob:
    EntityManager / Hibernate Session.
    """

    return SessionFactory()


def session_scope() -> Generator[Session, None, None]:
    """
    Kleine Utility-Funktion für später.

    Die Repositories können zunächst auch direkt create_session()
    verwenden.
    """

    session = create_session()

    try:
        yield session
    finally:
        session.close()
