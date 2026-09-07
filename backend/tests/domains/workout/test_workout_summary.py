from domains.workout.session import (
    WorkoutStatus,
)
from domains.workout.summary import (
    create_workout_summary,
)


def test_completed_workout_has_full_completion() -> None:
    summary = create_workout_summary(
        total_duration_minutes=30,
        elapsed_seconds=1800,
        distance_m=1234,
        status=WorkoutStatus.COMPLETED,
    )

    assert summary.planned_seconds == 1800
    assert summary.elapsed_seconds == 1800
    assert summary.distance_m == 1234
    assert summary.completion_percent == 100
    assert summary.status == WorkoutStatus.COMPLETED


def test_aborted_workout_has_partial_completion() -> None:
    summary = create_workout_summary(
        total_duration_minutes=30,
        elapsed_seconds=900,
        distance_m=2345,
        status=WorkoutStatus.ABORTED,
    )

    assert summary.planned_seconds == 1800
    assert summary.elapsed_seconds == 900
    assert summary.distance_m == 2345
    assert summary.completion_percent == 50
    assert summary.status == WorkoutStatus.ABORTED


def test_completion_is_limited_to_100_percent() -> None:
    summary = create_workout_summary(
        total_duration_minutes=30,
        elapsed_seconds=2000,
        distance_m=200,
        status=WorkoutStatus.COMPLETED,
    )

    assert summary.completion_percent == 100
