from datetime import UTC, datetime
from math import isfinite

from features.check_in.domain.check_in import CheckIn
from features.check_in.domain.repository import CheckInRepository


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
        current_weight_kg: float | None = None,
        sleep_hours: float | None = None,
        steps: int | None = None,
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

        # Optionale Tagesdaten werden nur geprüft, wenn ein Wert vorliegt.
        # None bedeutet "nicht erfasst" und ist ausdrücklich gültig.
        if current_weight_kg is not None and (
            not isfinite(current_weight_kg) or current_weight_kg <= 0 or current_weight_kg > 500
        ):
            raise InvalidCheckInError("current_weight_kg must be greater than 0 and at most 500")

        if sleep_hours is not None and (
            not isfinite(sleep_hours) or sleep_hours < 0 or sleep_hours > 24
        ):
            raise InvalidCheckInError("sleep_hours must be between 0 and 24")

        if steps is not None and steps < 0:
            raise InvalidCheckInError("steps must not be negative")

        check_in = CheckIn(
            person_id=person_id,
            timestamp=datetime.now(UTC),
            energy=energy,
            recovery=recovery,
            muscle_soreness=muscle_soreness,
            stress=stress,
            available_training_minutes=available_training_minutes,
            current_weight_kg=current_weight_kg,
            sleep_hours=sleep_hours,
            steps=steps,
        )

        self._repository.save(check_in)

        return check_in

    def get_latest(
        self,
        person_id: int,
    ) -> CheckIn | None:
        return self._repository.get_latest_for_person(person_id)

    def get_history(
        self,
        person_id: int,
        limit: int = 90,
    ) -> list[CheckIn]:
        if limit < 1 or limit > 1000:
            raise InvalidCheckInError("limit must be between 1 and 1000")

        return self._repository.get_history_for_person(person_id, limit)

    @staticmethod
    def _validate_scale(
        name: str,
        value: int,
    ) -> None:
        if value < 1 or value > 5:
            raise InvalidCheckInError(f"{name} must be between 1 and 5")
