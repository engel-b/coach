from datetime import UTC, datetime

from contracts.workout_mapper import to_workout_response
from domains.training.recommendation import (
    WorkoutPhase,
    WorkoutPhaseType,
)
from domains.workout.session import (
    WorkoutSession,
    WorkoutStatus,
)


def test_workout_is_mapped_to_response() -> None:
    started_at = datetime(
        2026,
        8,
        25,
        10,
        0,
        tzinfo=UTC,
    )

    workout = WorkoutSession(
        id="workout-1",
        person_id=1,
        started_at=started_at,
        status=WorkoutStatus.RUNNING,
        total_duration_minutes=30,
        elapsed_seconds=123,
        completed_at=None,
        phases=(
            WorkoutPhase(
                phase_type=WorkoutPhaseType.MAIN,
                duration_minutes=30,
                target_heart_rate_min=110,
                target_heart_rate_max=130,
            ),
        ),
    )

    response = to_workout_response(workout)

    assert response.id == "workout-1"
    assert response.person_id == 1
    assert response.status == "running"
    assert response.total_duration_minutes == 30
    assert response.elapsed_seconds == 123

    assert len(response.phases) == 1

    phase = response.phases[0]

    assert phase.phase_type == "main"
    assert phase.duration_minutes == 30
    assert phase.target_heart_rate_min == 110
    assert phase.target_heart_rate_max == 130
