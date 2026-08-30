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
        status=WorkoutStatus.COMPLETED,
    )

    assert summary.planned_seconds == 1800
    assert summary.elapsed_seconds == 1800
    assert summary.completion_percent == 100
    assert summary.status == WorkoutStatus.COMPLETED


def test_aborted_workout_has_partial_completion() -> None:
    summary = create_workout_summary(
        total_duration_minutes=30,
        elapsed_seconds=900,
        status=WorkoutStatus.ABORTED,
    )

    assert summary.planned_seconds == 1800
    assert summary.elapsed_seconds == 900
    assert summary.completion_percent == 50
    assert summary.status == WorkoutStatus.ABORTED


def test_completion_is_limited_to_100_percent() -> None:
    summary = create_workout_summary(
        total_duration_minutes=30,
        elapsed_seconds=2000,
        status=WorkoutStatus.COMPLETED,
    )

    assert summary.completion_percent == 100
