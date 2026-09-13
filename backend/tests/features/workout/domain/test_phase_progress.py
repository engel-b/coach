from datetime import UTC, datetime

import pytest

from features.training.domain.recommendation import (
    WorkoutPhase,
    WorkoutPhaseType,
)
from features.workout.domain.phase_progress import get_current_phase
from features.workout.domain.session import WorkoutSession, WorkoutStatus


def create_workout() -> WorkoutSession:
    return WorkoutSession(
        id="workout-1",
        person_id=1,
        started_at=datetime.now(UTC),
        status=WorkoutStatus.RUNNING,
        total_duration_minutes=30,
        phases=(
            WorkoutPhase(
                phase_type=WorkoutPhaseType.WARM_UP,
                duration_minutes=5,
                target_heart_rate_min=100,
                target_heart_rate_max=120,
            ),
            WorkoutPhase(
                phase_type=WorkoutPhaseType.MAIN,
                duration_minutes=20,
                target_heart_rate_min=125,
                target_heart_rate_max=145,
            ),
            WorkoutPhase(
                phase_type=WorkoutPhaseType.COOL_DOWN,
                duration_minutes=5,
                target_heart_rate_min=95,
                target_heart_rate_max=115,
            ),
        ),
    )


def test_first_phase_is_active_at_workout_start() -> None:
    progress = get_current_phase(
        create_workout(),
        elapsed_seconds=0,
    )

    assert progress is not None
    assert progress.phase.phase_type is WorkoutPhaseType.WARM_UP
    assert progress.phase_index == 0
    assert progress.phase_elapsed_seconds == 0
    assert progress.phase_remaining_seconds == 300


def test_second_phase_starts_exactly_after_first_phase() -> None:
    progress = get_current_phase(
        create_workout(),
        elapsed_seconds=300,
    )

    assert progress is not None
    assert progress.phase.phase_type is WorkoutPhaseType.MAIN
    assert progress.phase_index == 1
    assert progress.phase_elapsed_seconds == 0
    assert progress.phase_remaining_seconds == 1200


def test_progress_inside_main_phase_is_calculated() -> None:
    progress = get_current_phase(
        create_workout(),
        elapsed_seconds=420,
    )

    assert progress is not None
    assert progress.phase.phase_type is WorkoutPhaseType.MAIN
    assert progress.phase_elapsed_seconds == 120
    assert progress.phase_remaining_seconds == 1080


def test_last_second_belongs_to_cool_down() -> None:
    progress = get_current_phase(
        create_workout(),
        elapsed_seconds=1799,
    )

    assert progress is not None
    assert progress.phase.phase_type is WorkoutPhaseType.COOL_DOWN
    assert progress.phase_elapsed_seconds == 299
    assert progress.phase_remaining_seconds == 1


def test_no_phase_is_active_after_planned_workout_duration() -> None:
    progress = get_current_phase(
        create_workout(),
        elapsed_seconds=1800,
    )

    assert progress is None


def test_negative_elapsed_seconds_are_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="elapsed_seconds must not be negative",
    ):
        get_current_phase(
            create_workout(),
            elapsed_seconds=-1,
        )
