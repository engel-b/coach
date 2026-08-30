from collections.abc import Generator
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

# backend/adapters/persistence/database.py
#                ↓
# backend/
#                ↓
# Coach/
PROJECT_ROOT = Path(__file__).resolve().parents[3]

DATABASE_PATH = PROJECT_ROOT / "data" / "health-coach.db"

DATABASE_URL = f"sqlite:///{DATABASE_PATH}"


class Base(DeclarativeBase):
    """
    Basisklasse für alle SQLAlchemy-Tabellenmodelle.

    Java-/JPA-Vergleich:
    Die konkreten Klassen darunter entsprechen ungefähr @Entity-Klassen.
    """


engine = create_engine(
    DATABASE_URL,
    # SQLite erlaubt Verbindungen standardmäßig nur aus dem Thread,
    # der sie erzeugt hat. FastAPI kann Requests aber über verschiedene
    # Threads abwickeln.
    connect_args={
        "check_same_thread": False,
    },
)


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
