import pytest

from features.check_in.persistence.in_memory_check_in_repository import (
    InMemoryCheckInRepository,
)
from features.check_in.service.check_in_service import (
    CheckInService,
    InvalidCheckInError,
)


def test_check_in_is_created() -> None:
    repository = InMemoryCheckInRepository()
    service = CheckInService(repository)

    check_in = service.create(
        person_id=1,
        energy=4,
        recovery=3,
        muscle_soreness=2,
        stress=2,
        available_training_minutes=45,
    )

    assert check_in.person_id == 1
    assert check_in.energy == 4
    assert check_in.available_training_minutes == 45


def test_latest_check_in_can_be_loaded() -> None:
    repository = InMemoryCheckInRepository()
    service = CheckInService(repository)

    service.create(
        person_id=2,
        energy=3,
        recovery=4,
        muscle_soreness=1,
        stress=2,
        available_training_minutes=30,
    )

    latest = service.get_latest(2)

    assert latest is not None
    assert latest.person_id == 2
    assert latest.recovery == 4


def test_invalid_scale_is_rejected() -> None:
    repository = InMemoryCheckInRepository()
    service = CheckInService(repository)

    with pytest.raises(InvalidCheckInError):
        service.create(
            person_id=1,
            energy=6,
            recovery=3,
            muscle_soreness=2,
            stress=2,
            available_training_minutes=45,
        )


def test_invalid_training_time_is_rejected() -> None:
    repository = InMemoryCheckInRepository()
    service = CheckInService(repository)

    with pytest.raises(InvalidCheckInError):
        service.create(
            person_id=1,
            energy=4,
            recovery=3,
            muscle_soreness=2,
            stress=2,
            available_training_minutes=42,
        )
