import pytest

from features.training.domain.heart_rate_target_policy import HeartRateTargetPolicy
from features.training.domain.recommendation import WorkoutPhaseType, WorkoutType


def test_uses_heart_rate_reserve_when_resting_heart_rate_is_known() -> None:
    target = HeartRateTargetPolicy().calculate(
        workout_type=WorkoutType.BASE_ENDURANCE,
        phase_type=WorkoutPhaseType.MAIN,
        max_heart_rate_bpm=180,
        resting_heart_rate_bpm=70,
    )

    assert target.minimum_bpm == 114
    assert target.maximum_bpm == 130


def test_high_resting_heart_rate_is_capped_for_target_calculation() -> None:
    policy = HeartRateTargetPolicy()

    target_at_90 = policy.calculate(
        workout_type=WorkoutType.BASE_ENDURANCE,
        phase_type=WorkoutPhaseType.MAIN,
        max_heart_rate_bpm=180,
        resting_heart_rate_bpm=90,
    )
    target_at_100 = policy.calculate(
        workout_type=WorkoutType.BASE_ENDURANCE,
        phase_type=WorkoutPhaseType.MAIN,
        max_heart_rate_bpm=180,
        resting_heart_rate_bpm=100,
    )

    assert target_at_100 == target_at_90
    assert target_at_100.minimum_bpm == 126
    assert target_at_100.maximum_bpm == 140


def test_falls_back_to_previous_max_heart_rate_percentages_without_resting_rate() -> None:
    target = HeartRateTargetPolicy().calculate(
        workout_type=WorkoutType.BASE_ENDURANCE,
        phase_type=WorkoutPhaseType.MAIN,
        max_heart_rate_bpm=180,
        resting_heart_rate_bpm=None,
    )

    assert target.minimum_bpm == 108
    assert target.maximum_bpm == 126


def test_rejects_invalid_resting_heart_rate_reference() -> None:
    with pytest.raises(ValueError):
        HeartRateTargetPolicy().calculate(
            workout_type=WorkoutType.BASE_ENDURANCE,
            phase_type=WorkoutPhaseType.MAIN,
            max_heart_rate_bpm=80,
            resting_heart_rate_bpm=100,
        )


def test_describes_heart_rate_reserve_basis_and_capped_reference() -> None:
    basis = HeartRateTargetPolicy().describe_basis(
        max_heart_rate_bpm=180,
        resting_heart_rate_bpm=98,
    )

    assert basis.method.value == "heart_rate_reserve"
    assert basis.max_heart_rate_bpm == 180
    assert basis.resting_heart_rate_bpm == 98
    assert basis.reference_resting_heart_rate_bpm == 90


def test_describes_max_heart_rate_fallback_without_resting_rate() -> None:
    basis = HeartRateTargetPolicy().describe_basis(
        max_heart_rate_bpm=180,
        resting_heart_rate_bpm=None,
    )

    assert basis.method.value == "max_heart_rate_percentage"
    assert basis.reference_resting_heart_rate_bpm is None
