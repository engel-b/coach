from collections.abc import Iterator
from datetime import date
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import apps.api.main as api_main
from adapters.persistence.database import Base
from adapters.persistence.sqlalchemy_person_profile_repository import (
    SqlAlchemyPersonProfileRepository,
)
from adapters.persistence.sqlalchemy_person_profile_writer import (
    SqlAlchemyPersonProfileWriter,
)
from adapters.persistence.sqlalchemy_person_repository import (
    SqlAlchemyPersonRepository,
)
from application.person.management_service import PersonManagementService
from application.person.person_service import PersonService
from application.person.profile_service import PersonProfileService
from domains.person.person import Person
from domains.person.profile import PersonProfile, TrainingGoal


@pytest.fixture
def profile_api(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> Iterator[TestClient]:
    # Eine eigene SQLite-Datei pro Test. Keine echte Coach-Datenbank.
    engine = create_engine(
        f"sqlite:///{tmp_path / 'profile-api.db'}",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)

    factory = sessionmaker(bind=engine, expire_on_commit=False)

    person_repository = SqlAlchemyPersonRepository(
        session_factory=factory,
    )
    profile_repository = SqlAlchemyPersonProfileRepository(
        session_factory=factory,
    )
    writer = SqlAlchemyPersonProfileWriter(
        session_factory=factory,
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

    monkeypatch.setattr(
        api_main,
        "person_service",
        PersonService(repository=person_repository),
    )
    monkeypatch.setattr(
        api_main,
        "person_profile_service",
        PersonProfileService(repository=profile_repository),
    )
    monkeypatch.setattr(
        api_main,
        "person_management_service",
        PersonManagementService(
            person_repository=person_repository,
            profile_writer=writer,
        ),
    )

    with TestClient(api_main.app) as client:
        yield client

    engine.dispose()


def valid_profile_request() -> dict[str, object]:
    return {
        "displayName": "Neuer Name",
        "dateOfBirth": "1985-05-10",
        "heightCm": 175,
        "trainingGoal": "weight_loss",
        "maxHeartRateBpm": 190,
        "startWeightKg": 92.5,
        "targetWeightKg": 82.0,
    }


def test_get_profile_returns_camel_case(
    profile_api: TestClient,
) -> None:
    response = profile_api.get("/api/persons/1/profile")

    assert response.status_code == 200
    assert response.json() == {
        "personId": 1,
        "displayName": "Person 1",
        "dateOfBirth": "1980-01-01",
        "heightCm": 180,
        "trainingGoal": "general_fitness",
        "maxHeartRateBpm": None,
        "startWeightKg": None,
        "targetWeightKg": None,
    }


def test_put_profile_updates_name_and_profile(
    profile_api: TestClient,
) -> None:
    response = profile_api.put(
        "/api/persons/1/profile",
        json=valid_profile_request(),
    )

    assert response.status_code == 200
    assert response.json() == {
        "personId": 1,
        **valid_profile_request(),
    }

    # Ein neuer HTTP-Request liest die gespeicherten Daten erneut.
    profile_response = profile_api.get("/api/persons/1/profile")
    assert profile_response.status_code == 200
    assert profile_response.json() == response.json()

    # Auch die Personenliste muss den neuen Namen liefern.
    persons_response = profile_api.get("/api/persons")
    assert persons_response.status_code == 200
    assert persons_response.json() == [{"id": 1, "displayName": "Neuer Name"}]


def test_get_unknown_person_returns_404(
    profile_api: TestClient,
) -> None:
    response = profile_api.get("/api/persons/999/profile")

    assert response.status_code == 404
    assert response.json()["detail"] == "Person not found"


def test_put_unknown_person_returns_404(
    profile_api: TestClient,
) -> None:
    response = profile_api.put(
        "/api/persons/999/profile",
        json=valid_profile_request(),
    )

    assert response.status_code == 404


def test_weight_loss_requires_both_weights(
    profile_api: TestClient,
) -> None:
    request = valid_profile_request()
    request["startWeightKg"] = None

    response = profile_api.put(
        "/api/persons/1/profile",
        json=request,
    )

    assert response.status_code == 422

    # Die fehlgeschlagene Anfrage darf nichts verändert haben.
    saved = profile_api.get("/api/persons/1/profile").json()
    assert saved["displayName"] == "Person 1"
    assert saved["trainingGoal"] == "general_fitness"


def test_weight_loss_target_must_be_lower(
    profile_api: TestClient,
) -> None:
    request = valid_profile_request()
    request["targetWeightKg"] = 100.0

    response = profile_api.put(
        "/api/persons/1/profile",
        json=request,
    )

    assert response.status_code == 422

    saved = profile_api.get("/api/persons/1/profile").json()
    assert saved["displayName"] == "Person 1"
    assert saved["startWeightKg"] is None


def test_blank_display_name_is_rejected(
    profile_api: TestClient,
) -> None:
    request = valid_profile_request()
    request["displayName"] = "   "

    response = profile_api.put(
        "/api/persons/1/profile",
        json=request,
    )

    assert response.status_code == 422


def test_future_birth_date_is_rejected(
    profile_api: TestClient,
) -> None:
    request = valid_profile_request()
    request["dateOfBirth"] = "2099-01-01"

    response = profile_api.put(
        "/api/persons/1/profile",
        json=request,
    )

    assert response.status_code == 422

    saved = profile_api.get("/api/persons/1/profile").json()
    assert saved["displayName"] == "Person 1"
