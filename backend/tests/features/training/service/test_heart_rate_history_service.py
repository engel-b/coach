from datetime import UTC, datetime, timedelta

from features.training.domain.heart_rate_history import (
    HeartRateHistoryRules,
    HeartRateHistoryStatus,
)
from features.training.service.heart_rate_history_service import HeartRateHistoryService
from features.workout.domain.heart_rate_summary import WorkoutHeartRateSummary
from features.workout.domain.session import WorkoutSession, WorkoutStatus


def workout(
    index: int,
    *,
    in_target: int,
    above: int,
    below: int,
    sample_count: int = 120,
    status: WorkoutStatus = WorkoutStatus.COMPLETED,
) -> WorkoutSession:
    return WorkoutSession(
        id=f"workout-{index}",
        person_id=1,
        started_at=datetime(2026, 9, 20, 10, 0, tzinfo=UTC) - timedelta(days=index),
        status=status,
        phases=(),
        total_duration_minutes=30,
        elapsed_seconds=1800,
        heart_rate_summary=WorkoutHeartRateSummary(
            sample_count=sample_count,
            average_bpm=135,
            max_bpm=155,
            below_target_percent=below,
            in_target_percent=in_target,
            above_target_percent=above,
        ),
    )


def service() -> HeartRateHistoryService:
    return HeartRateHistoryService(
        rules=HeartRateHistoryRules(
            lookback_workouts=6,
            min_workout_count=3,
            min_samples_per_workout=30,
            mostly_in_target_percent=60,
            dominant_outside_target_percent=40,
            high_response_duration_cap_minutes=30,
        )
    )


def test_high_response_caps_duration_conservatively() -> None:
    result = service().analyze(
        workouts=[
            workout(1, in_target=40, above=50, below=10),
            workout(2, in_target=45, above=45, below=10),
            workout(3, in_target=50, above=40, below=10),
        ]
    )

    assert result.status is HeartRateHistoryStatus.MOSTLY_ABOVE_TARGET
    assert result.workout_count == 3
    assert result.median_above_target_percent == 45
    assert result.max_duration_minutes == 30


def test_in_target_history_does_not_raise_training_load() -> None:
    result = service().analyze(
        workouts=[
            workout(1, in_target=70, above=20, below=10),
            workout(2, in_target=65, above=20, below=15),
            workout(3, in_target=75, above=15, below=10),
        ]
    )

    assert result.status is HeartRateHistoryStatus.MOSTLY_IN_TARGET
    assert result.max_duration_minutes is None


def test_below_target_history_never_increases_intensity() -> None:
    result = service().analyze(
        workouts=[
            workout(1, in_target=40, above=10, below=50),
            workout(2, in_target=45, above=10, below=45),
            workout(3, in_target=50, above=10, below=40),
        ]
    )

    assert result.status is HeartRateHistoryStatus.MOSTLY_BELOW_TARGET
    assert result.max_duration_minutes is None


def test_insufficient_or_low_sample_workouts_are_ignored() -> None:
    result = service().analyze(
        workouts=[
            workout(1, in_target=40, above=50, below=10, sample_count=10),
            workout(2, in_target=40, above=50, below=10),
            workout(3, in_target=40, above=50, below=10, status=WorkoutStatus.ABORTED),
        ]
    )

    assert result.status is HeartRateHistoryStatus.INSUFFICIENT_DATA
    assert result.workout_count == 1
