from dataclasses import replace
from datetime import date

import pytest

from domains.person.profile import PersonProfile, TrainingGoal
from domains.person.profile_validation import (
    InvalidPersonProfileError,
    validate_person_profile,
)


def make_profile() -> PersonProfile:
    return PersonProfile(
        person_id=1,
        date_of_birth=date(1980, 1, 1),
        height_cm=180,
        training_goal=TrainingGoal.GENERAL_FITNESS,
    )


def test_general_fitness_allows_optional_weights() -> None:
    validate_person_profile(make_profile())


def test_weight_loss_requires_both_weights() -> None:
    profile = replace(
        make_profile(),
        training_goal=TrainingGoal.WEIGHT_LOSS,
    )

    with pytest.raises(
        InvalidPersonProfileError,
        match="Start- und Zielgewicht",
    ):
        validate_person_profile(profile)


def test_weight_loss_target_must_be_lower() -> None:
    profile = replace(
        make_profile(),
        training_goal=TrainingGoal.WEIGHT_LOSS,
        start_weight_kg=90,
        target_weight_kg=95,
    )

    with pytest.raises(
        InvalidPersonProfileError,
        match="unter dem Startgewicht",
    ):
        validate_person_profile(profile)


def test_weight_loss_accepts_valid_weights() -> None:
    profile = replace(
        make_profile(),
        training_goal=TrainingGoal.WEIGHT_LOSS,
        start_weight_kg=95.5,
        target_weight_kg=82,
    )

    validate_person_profile(profile)


def test_future_birth_date_is_rejected() -> None:
    profile = replace(
        make_profile(),
        date_of_birth=date(2099, 1, 1),
    )

    with pytest.raises(InvalidPersonProfileError):
        validate_person_profile(profile)