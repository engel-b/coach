from features.training.domain.load_response import LoadResponseStatus
from features.training.domain.recommendation import WorkoutType
from features.workout.domain.adaptive_evaluation import WorkoutExpectation, evaluate_workout
from features.workout.domain.bike_summary import WorkoutBikeSummary
from features.workout.domain.heart_rate_summary import WorkoutHeartRateSummary


def test_compares_main_phase_to_frozen_pre_workout_baseline() -> None:
    baseline = WorkoutExpectation(
        WorkoutType.BASE_ENDURANCE, LoadResponseStatus.HIGHER_HR_AT_SIMILAR_LOAD, 5, 10, 100
    )
    hr = WorkoutHeartRateSummary(40, 135, 160, 5, 60, 35)
    bike = WorkoutBikeSummary(40, 105, 40, 72)

    evaluation = evaluate_workout(baseline, hr, bike)

    assert evaluation is not None
    assert evaluation.heart_rate_response == "higher"
    assert evaluation.power_response == "similar"
    assert evaluation.expectation_match == "matched"


def test_changed_power_prevents_claim_about_expected_heart_rate() -> None:
    baseline = WorkoutExpectation(WorkoutType.BASE_ENDURANCE, LoadResponseStatus.STABLE, 5, 0, 100)
    hr = WorkoutHeartRateSummary(40, 145, 160, 0, 60, 40)
    bike = WorkoutBikeSummary(40, 150, 40, 72)

    evaluation = evaluate_workout(baseline, hr, bike)

    assert evaluation is not None
    assert evaluation.power_response == "higher"
    assert evaluation.expectation_match == "not_comparable"


def test_missing_data_stays_unknown() -> None:
    baseline = WorkoutExpectation(WorkoutType.BASE_ENDURANCE, LoadResponseStatus.STABLE, 5, 0, 100)
    evaluation = evaluate_workout(baseline, None, None)
    assert evaluation is not None
    assert evaluation.expectation_match == "insufficient_data"
