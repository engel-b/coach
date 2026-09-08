from collections.abc import Iterator
from datetime import date
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from adapters.persistence.database import Base
from adapters.persistence.person_model import PersonModel, PersonProfileModel
from adapters.persistence.sqlalchemy_person_profile_repository import (
    SqlAlchemyPersonProfileRepository,
)
from adapters.persistence.sqlalchemy_person_repository import (
    SqlAlchemyPersonRepository,
)
from domains.person.person import Person
from domains.person.profile import PersonProfile, TrainingGoal


@pytest.fixture
def session_factory(
    tmp_path: Path,
) -> Iterator[sessionmaker[Session]]:
    database_path = tmp_path / "persons.db"

    engine = create_engine(
        f"sqlite:///{database_path}",
        connect_args={"check_same_thread": False},
    )

    # Die Namen stellen sicher, dass die Models in Base.metadata registriert sind.
    assert PersonModel.__tablename__ == "person"
    assert PersonProfileModel.__tablename__ == "person_profile"

    Base.metadata.create_all(engine)

    factory = sessionmaker(
        bind=engine,
        expire_on_commit=False,
    )

    yield factory

    engine.dispose()


def test_person_repository_saves_and_loads_person(
    session_factory: sessionmaker[Session],
) -> None:
    repository = SqlAlchemyPersonRepository(
        session_factory=session_factory,
    )

    repository.save(
        Person(
            id=1,
            display_name="Person 1",
        )
    )

    person = repository.get(1)

    assert person == Person(
        id=1,
        display_name="Person 1",
    )


def test_person_repository_updates_display_name(
    session_factory: sessionmaker[Session],
) -> None:
    repository = SqlAlchemyPersonRepository(
        session_factory=session_factory,
    )

    repository.save(Person(id=1, display_name="Person 1"))
    repository.save(Person(id=1, display_name="Neuer Name"))

    person = repository.get(1)

    assert person == Person(
        id=1,
        display_name="Neuer Name",
    )


def test_person_repository_returns_persons_sorted_by_id(
    session_factory: sessionmaker[Session],
) -> None:
    repository = SqlAlchemyPersonRepository(
        session_factory=session_factory,
    )

    repository.save(Person(id=3, display_name="Person 3"))
    repository.save(Person(id=1, display_name="Person 1"))
    repository.save(Person(id=2, display_name="Person 2"))

    persons = repository.get_all()

    assert [person.id for person in persons] == [1, 2, 3]


def test_person_profile_repository_saves_and_loads_profile(
    session_factory: sessionmaker[Session],
) -> None:
    person_repository = SqlAlchemyPersonRepository(
        session_factory=session_factory,
    )
    profile_repository = SqlAlchemyPersonProfileRepository(
        session_factory=session_factory,
    )

    person_repository.save(Person(id=1, display_name="Person 1"))

    profile = PersonProfile(
        person_id=1,
        date_of_birth=date(1980, 1, 1),
        height_cm=180,
        training_goal=TrainingGoal.WEIGHT_LOSS,
        max_heart_rate_bpm=185,
        start_weight_kg=95.5,
        target_weight_kg=82.0,
    )

    profile_repository.save(profile)

    assert profile_repository.get(1) == profile


def test_person_profile_repository_updates_profile(
    session_factory: sessionmaker[Session],
) -> None:
    person_repository = SqlAlchemyPersonRepository(
        session_factory=session_factory,
    )
    profile_repository = SqlAlchemyPersonProfileRepository(
        session_factory=session_factory,
    )

    person_repository.save(Person(id=1, display_name="Person 1"))

    profile_repository.save(
        PersonProfile(
            person_id=1,
            date_of_birth=date(1980, 1, 1),
            height_cm=180,
            training_goal=TrainingGoal.GENERAL_FITNESS,
        )
    )

    updated = PersonProfile(
        person_id=1,
        date_of_birth=date(1980, 1, 1),
        height_cm=181,
        training_goal=TrainingGoal.MUSCLE_GAIN,
        start_weight_kg=80.0,
        target_weight_kg=85.0,
    )

    profile_repository.save(updated)

    assert profile_repository.get(1) == updated
