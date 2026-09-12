from collections.abc import Iterator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from adapters.persistence.database import Base, enable_sqlite_foreign_keys
from features.check_in.persistence.check_in_model import CheckInModel
from features.person.persistence.person_model import PersonModel, PersonProfileModel
from features.workout.persistence.workout_model import WorkoutModel, WorkoutPhaseModel
from features.workout.persistence.workout_video_model import WorkoutVideoModel


@pytest.fixture
def session_factory() -> Iterator[sessionmaker[Session]]:
    """Create one isolated SQLite in-memory database per test.

    StaticPool keeps all sessions on the same in-memory database. Foreign-key
    enforcement is enabled so persistence tests behave like the productive
    SQLite setup.
    """

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    enable_sqlite_foreign_keys(engine)

    # Importing the model classes above registers every table in Base.metadata.
    assert CheckInModel.__tablename__ == "check_in"
    assert PersonModel.__tablename__ == "person"
    assert PersonProfileModel.__tablename__ == "person_profile"
    assert WorkoutModel.__tablename__ == "workout"
    assert WorkoutPhaseModel.__tablename__ == "workout_phase"
    assert WorkoutVideoModel.__tablename__ == "workout_video"

    Base.metadata.create_all(engine)

    factory = sessionmaker(
        bind=engine,
        expire_on_commit=False,
    )

    yield factory

    engine.dispose()
