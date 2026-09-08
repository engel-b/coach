from collections.abc import Iterator
from datetime import date
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from adapters.persistence.database import Base
from adapters.persistence.person_model import PersonModel, PersonProfileModel
from adapters.persistence.sqlalchemy_person_profile_writer import (
    SqlAlchemyPersonProfileWriter,
)
from domains.person.person import Person
from domains.person.profile import PersonProfile, TrainingGoal


@pytest.fixture
def session_factory(
    tmp_path: Path,
) -> Iterator[sessionmaker[Session]]:
    engine = create_engine(
        f"sqlite:///{tmp_path / 'person-profile-writer.db'}",
        connect_args={"check_same_thread": False},
    )

    Base.metadata.create_all(engine)

    factory = sessionmaker(
        bind=engine,
        expire_on_commit=False,
    )

    yield factory

    engine.dispose()


def seed_person_and_profile(
    session_factory: sessionmaker[Session],
) -> None:
    with session_factory() as session:
        session.add(
            PersonModel(
                id=1,
                display_name="Person 1",
            )
        )
        session.add(
            PersonProfileModel(
                person_id=1,
                date_of_birth=date(1980, 1, 1),
                height_cm=180,
                training_goal=TrainingGoal.GENERAL_FITNESS.value,
                max_heart_rate_bpm=None,
                start_weight_kg=None,
                target_weight_kg=None,
            )
        )
        session.commit()


def test_saves_person_name_and_profile_together(
    session_factory: sessionmaker[Session],
) -> None:
    seed_person_and_profile(session_factory)

    writer = SqlAlchemyPersonProfileWriter(
        session_factory=session_factory,
    )

    person = Person(
        id=1,
        display_name="Neuer Name",
    )

    profile = PersonProfile(
        person_id=1,
        date_of_birth=date(1985, 5, 10),
        height_cm=175,
        training_goal=TrainingGoal.WEIGHT_LOSS,
        max_heart_rate_bpm=190,
        start_weight_kg=92.5,
        target_weight_kg=82.0,
    )

    writer.save(person, profile)

    with session_factory() as session:
        saved_person = session.get(PersonModel, 1)
        saved_profile = session.get(PersonProfileModel, 1)

        assert saved_person is not None
        assert saved_person.display_name == "Neuer Name"

        assert saved_profile is not None
        assert saved_profile.date_of_birth == date(1985, 5, 10)
        assert saved_profile.height_cm == 175
        assert (
            saved_profile.training_goal
            == TrainingGoal.WEIGHT_LOSS.value
        )
        assert saved_profile.max_heart_rate_bpm == 190
        assert saved_profile.start_weight_kg == 92.5
        assert saved_profile.target_weight_kg == 82.0


def test_missing_person_does_not_create_profile(
    session_factory: sessionmaker[Session],
) -> None:
    writer = SqlAlchemyPersonProfileWriter(
        session_factory=session_factory,
    )

    person = Person(
        id=999,
        display_name="Unbekannt",
    )

    profile = PersonProfile(
        person_id=999,
        date_of_birth=date(1980, 1, 1),
        height_cm=180,
        training_goal=TrainingGoal.GENERAL_FITNESS,
    )

    with pytest.raises(
        ValueError,
        match="Person not found",
    ):
        writer.save(person, profile)

    with session_factory() as session:
        assert session.get(PersonModel, 999) is None
        assert session.get(PersonProfileModel, 999) is None


def test_rejects_mismatching_person_ids(
    session_factory: sessionmaker[Session],
) -> None:
    seed_person_and_profile(session_factory)

    writer = SqlAlchemyPersonProfileWriter(
        session_factory=session_factory,
    )

    person = Person(
        id=1,
        display_name="Person 1",
    )

    profile = PersonProfile(
        person_id=2,
        date_of_birth=date(1980, 1, 1),
        height_cm=180,
        training_goal=TrainingGoal.GENERAL_FITNESS,
    )

    with pytest.raises(
        ValueError,
        match="must match",
    ):
        writer.save(person, profile)

    with session_factory() as session:
        saved_person = session.get(PersonModel, 1)

        assert saved_person is not None
        assert saved_person.display_name == "Person 1"
        assert session.get(PersonProfileModel, 2) is None