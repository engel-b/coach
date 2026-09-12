from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from apps.api import main, wiring
from features.check_in.domain.check_in import CheckIn
from features.check_in.persistence.in_memory_check_in_repository import InMemoryCheckInRepository
from features.check_in.persistence.sqlalchemy_check_in_repository import SqlAlchemyCheckInRepository
from features.check_in.service.check_in_service import CheckInService, InvalidCheckInError
from features.person.domain.person import Person
from features.person.persistence.sqlalchemy_person_repository import SqlAlchemyPersonRepository


def sample(person_id: int, minute: int, weight: float | None) -> CheckIn:
    return CheckIn(
        person_id=person_id,
        timestamp=datetime(2026, 9, 1, tzinfo=UTC) + timedelta(minutes=minute),
        energy=4,
        recovery=4,
        muscle_soreness=2,
        stress=2,
        available_training_minutes=45,
        current_weight_kg=weight,
    )


def test_history_is_isolated_ordered_and_limited() -> None:
    repository = InMemoryCheckInRepository()
    service = CheckInService(repository)
    for check_in in [sample(1, 1, None), sample(2, 4, 90), sample(1, 3, 82), sample(1, 2, 83)]:
        repository.save(check_in)

    assert [item.current_weight_kg for item in service.get_history(1, 2)] == [82, 83]
    assert service.get_history(3) == []
    assert service.get_history(2)[0].person_id == 2
    with pytest.raises(InvalidCheckInError):
        service.get_history(1, 0)
    with pytest.raises(InvalidCheckInError):
        service.get_history(1, 1001)


def test_sqlalchemy_history_uses_isolated_database(
    session_factory: sessionmaker[Session],
) -> None:
    person_repository = SqlAlchemyPersonRepository(
        session_factory=session_factory,
    )
    person_repository.save(Person(id=1, display_name="Person 1"))
    person_repository.save(Person(id=2, display_name="Person 2"))

    repository = SqlAlchemyCheckInRepository(
        session_factory=session_factory,
    )

    for check_in in [
        sample(1, 1, None),
        sample(2, 4, 90),
        sample(1, 3, 82),
        sample(1, 2, 83),
    ]:
        repository.save(check_in)

    assert [item.current_weight_kg for item in repository.get_history_for_person(1, 2)] == [82, 83]
    assert repository.get_history_for_person(3, 90) == []

    latest = repository.get_latest_for_person(1)
    assert latest is not None
    assert latest.current_weight_kg == 82


def test_history_api(monkeypatch) -> None:
    from unittest.mock import Mock

    repository = InMemoryCheckInRepository()
    repository.save(sample(1, 1, None))
    repository.save(sample(1, 2, 82.4))
    person_service = Mock()
    person_service.get_person.side_effect = lambda person_id: (
        Person(id=1, display_name="Test") if person_id == 1 else None
    )
    monkeypatch.setattr(wiring, "person_service", person_service)
    monkeypatch.setattr(wiring, "check_in_service", CheckInService(repository))

    with TestClient(main.app) as client:
        response = client.get("/api/persons/1/check-ins?limit=1")
        assert response.status_code == 200
        assert len(response.json()) == 1
        assert response.json()[0]["currentWeightKg"] == 82.4
        assert response.json()[0]["sleepHours"] is None
        assert client.get("/api/persons/2/check-ins").status_code == 404
        assert client.get("/api/persons/1/check-ins?limit=0").status_code == 422
        assert client.get("/api/persons/1/check-ins?limit=1001").status_code == 422
