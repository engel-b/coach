from datetime import UTC, datetime

from domains.check_in.check_in import CheckIn
from domains.check_in.repository import CheckInRepository


class InvalidCheckInError(ValueError):
    """
    Wird ausgelöst, wenn ein Check-in fachlich ungültige Werte enthält.
    """


class CheckInService:
    """
    Application Service für Check-ins.

    Hier liegen die Regeln für die Erstellung eines Check-ins.
    """

    def __init__(
        self,
        repository: CheckInRepository,
    ) -> None:
        self._repository = repository

    def create(
        self,
        *,
        person_id: int,
        energy: int,
        recovery: int,
        muscle_soreness: int,
        stress: int,
        available_training_minutes: int,
    ) -> CheckIn:
        self._validate_scale("energy", energy)
        self._validate_scale("recovery", recovery)
        self._validate_scale(
            "muscle_soreness",
            muscle_soreness,
        )
        self._validate_scale("stress", stress)

        if available_training_minutes not in {
            15,
            30,
            45,
            60,
        }:
            raise InvalidCheckInError("available_training_minutes must be 15, 30, 45 or 60")

        check_in = CheckIn(
            person_id=person_id,
            timestamp=datetime.now(UTC),
            energy=energy,
            recovery=recovery,
            muscle_soreness=muscle_soreness,
            stress=stress,
            available_training_minutes=(available_training_minutes),
        )

        self._repository.save(check_in)

        return check_in

    def get_latest(
        self,
        person_id: int,
    ) -> CheckIn | None:
        return self._repository.get_latest_for_person(person_id)

    @staticmethod
    def _validate_scale(
        name: str,
        value: int,
    ) -> None:
        if value < 1 or value > 5:
            raise InvalidCheckInError(f"{name} must be between 1 and 5")
