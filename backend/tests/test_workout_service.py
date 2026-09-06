from adapters.persistence.in_memory_workout_repository import (
    InMemoryWorkoutRepository,
)
from application.workout.service import WorkoutService
from domains.training.recommendation import (
    TrainingRecommendation,
    WorkoutPhase,
    WorkoutPhaseType,
    WorkoutType,
)
from domains.workout.session import WorkoutStatus


def create_recommendation() -> TrainingRecommendation:
    return TrainingRecommendation(
        workout_type=WorkoutType.BASE_ENDURANCE,
        total_duration_minutes=30,
        reason="Test",
        phases=(
            WorkoutPhase(
                phase_type=WorkoutPhaseType.WARM_UP,
                duration_minutes=5,
                target_heart_rate_min=90,
                target_heart_rate_max=110,
            ),
            WorkoutPhase(
                phase_type=WorkoutPhaseType.MAIN,
                duration_minutes=20,
                target_heart_rate_min=110,
                target_heart_rate_max=130,
            ),
            WorkoutPhase(
                phase_type=WorkoutPhaseType.COOL_DOWN,
                duration_minutes=5,
                target_heart_rate_min=90,
                target_heart_rate_max=110,
            ),
        ),
    )


def test_workout_can_be_started() -> None:
    repository = InMemoryWorkoutRepository()
    service = WorkoutService(repository)

    workout = service.start(
        person_id=1,
        recommendation=create_recommendation(),
    )

    assert workout.person_id == 1
    assert workout.status == WorkoutStatus.RUNNING
    assert len(workout.phases) == 3


def test_workout_can_be_completed() -> None:
    repository = InMemoryWorkoutRepository()
    service = WorkoutService(repository)

    workout = service.start(
        person_id=1,
        recommendation=create_recommendation(),
    )

    completed = service.complete(
        workout.id,
        elapsed_seconds=1800,
        distance_m=12345,
    )

    assert completed.status == WorkoutStatus.COMPLETED
    assert completed.elapsed_seconds == 1800
    assert completed.distance_m == 12345
    assert completed.completed_at is not None


def test_workout_can_be_aborted() -> None:
    repository = InMemoryWorkoutRepository()
    service = WorkoutService(repository)

    workout = service.start(
        person_id=1,
        recommendation=create_recommendation(),
    )

    aborted = service.abort(
        workout.id,
        elapsed_seconds=723,
        distance_m=4321,
    )

    assert aborted.status == WorkoutStatus.ABORTED
    assert aborted.elapsed_seconds == 723
    assert aborted.distance_m == 4321
    assert aborted.completed_at is not None
