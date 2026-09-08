from datetime import date

from features.person.domain.profile import PersonProfile, TrainingGoal
from features.training.domain.heart_rate import (
    calculate_age,
    estimate_max_heart_rate,
    get_max_heart_rate,
)


def test_age_after_birthday() -> None:
    age = calculate_age(
        date_of_birth=date(1980, 5, 10),
        on_date=date(2026, 8, 24),
    )

    assert age == 46


def test_age_before_birthday() -> None:
    age = calculate_age(
        date_of_birth=date(1980, 12, 10),
        on_date=date(2026, 8, 24),
    )

    assert age == 45


def test_max_heart_rate_is_estimated_from_age() -> None:
    assert estimate_max_heart_rate(40) == 180


def test_known_max_heart_rate_has_priority() -> None:
    profile = PersonProfile(
        person_id=1,
        date_of_birth=date(1980, 1, 1),
        height_cm=180,
        training_goal=TrainingGoal.ENDURANCE,
        max_heart_rate_bpm=192,
    )

    result = get_max_heart_rate(
        profile,
        date(2026, 8, 24),
    )

    assert result == 192
