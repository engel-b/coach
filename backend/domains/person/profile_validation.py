from datetime import UTC, datetime
from math import isfinite

from domains.person.profile import PersonProfile, TrainingGoal


class InvalidPersonProfileError(ValueError):
    pass


def validate_person_profile(profile: PersonProfile) -> None:
    """Prüft fachliche Regeln unabhängig von HTTP und Datenbank."""

    today = datetime.now(UTC).date()

    if profile.date_of_birth > today:
        raise InvalidPersonProfileError(
            "Das Geburtsdatum darf nicht in der Zukunft liegen."
        )

    if not 100 <= profile.height_cm <= 250:
        raise InvalidPersonProfileError(
            "Die Größe muss zwischen 100 und 250 cm liegen."
        )

    if (
        profile.max_heart_rate_bpm is not None
        and not 100 <= profile.max_heart_rate_bpm <= 230
    ):
        raise InvalidPersonProfileError(
            "Der Maximalpuls muss zwischen 100 und 230 liegen."
        )

    for weight in (
        profile.start_weight_kg,
        profile.target_weight_kg,
    ):
        if (
            weight is not None
            and (not isfinite(weight) or not 0 < weight <= 500)
        ):
            raise InvalidPersonProfileError(
                "Gewichte müssen größer als 0 und höchstens 500 kg sein."
            )

    if profile.training_goal == TrainingGoal.WEIGHT_LOSS:
        if (
            profile.start_weight_kg is None
            or profile.target_weight_kg is None
        ):
            raise InvalidPersonProfileError(
                "Für Abnehmen sind Start- und Zielgewicht erforderlich."
            )

        if profile.target_weight_kg >= profile.start_weight_kg:
            raise InvalidPersonProfileError(
                "Das Zielgewicht muss unter dem Startgewicht liegen."
            )