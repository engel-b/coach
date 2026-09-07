from datetime import UTC, datetime
import pytest

from adapters.persistence.in_memory_workout_repository import InMemoryWorkoutRepository
from application.workout.service import InvalidWorkoutVideoError, WorkoutService
from domains.training.recommendation import (
    TrainingRecommendation,
    WorkoutPhase,
    WorkoutPhaseType,
    WorkoutType,
)
from domains.workout.session import WorkoutSession, WorkoutStatus
from domains.workout.video import WorkoutVideo


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


def test_checkpoint_updates_running_workout() -> None:
    repository = InMemoryWorkoutRepository()
    service = WorkoutService(repository=repository)

    workout = WorkoutSession(
        id="workout-checkpoint-test",
        person_id=1,
        started_at=datetime.now(UTC),
        status=WorkoutStatus.RUNNING,
        phases=(),
        total_duration_minutes=30,
    )

    repository.save(workout)

    updated = service.checkpoint(
        workout.id,
        elapsed_seconds=120,
        distance_m=1350,
        video_position_seconds=87.5,
    )

    assert updated.status == WorkoutStatus.RUNNING
    assert updated.elapsed_seconds == 120
    assert updated.distance_m == 1350
    assert updated.video_position_seconds == 87.5

    persisted = repository.get(workout.id)

    assert persisted is not None
    assert persisted.elapsed_seconds == 120
    assert persisted.distance_m == 1350
    assert persisted.video_position_seconds == 87.5


def test_new_workout_resumes_video_from_previous_workout() -> None:
    repository = InMemoryWorkoutRepository()
    service = WorkoutService(repository=repository)

    first_workout = service.start(
        person_id=1,
        recommendation=create_recommendation(),
    )

    service.checkpoint(
        first_workout.id,
        elapsed_seconds=120,
        distance_m=1350,
        video_position_seconds=87.5,
    )

    second_workout = service.start(
        person_id=1,
        recommendation=create_recommendation(),
    )

    assert second_workout.video_id == first_workout.video_id
    assert second_workout.video_position_seconds == 87.5


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


def test_start_with_same_selected_video_resumes_previous_position() -> None:
    workout_repository = InMemoryWorkoutRepository()
    video_repository = InMemoryWorkoutVideoRepository()

    video_repository.save(
        WorkoutVideo(
            id="cycling-alpen-01",
            title="Alpen",
            description="Trainingsvideo Alpen",
            file_path="cycling/alpen.mp4",
            duration_seconds=3600,
            active=True,
            created_at=datetime.now(UTC),
        )
    )

    service = WorkoutService(
        repository=workout_repository,
        video_repository=video_repository,
    )

    first_workout = service.start(
        person_id=1,
        recommendation=RECOMMENDATION,
        video_id="cycling-alpen-01",
    )

    service.checkpoint(
        first_workout.id,
        elapsed_seconds=60,
        distance_m=500,
        video_position_seconds=87.5,
    )

    second_workout = service.start(
        person_id=1,
        recommendation=RECOMMENDATION,
        video_id="cycling-alpen-01",
    )

    assert second_workout.video_id == "cycling-alpen-01"
    assert second_workout.video_position_seconds == 87.5


def test_start_with_different_selected_video_starts_at_zero() -> None:
    workout_repository = InMemoryWorkoutRepository()
    video_repository = InMemoryWorkoutVideoRepository()

    video_repository.save(
        WorkoutVideo(
            id="cycling-alpen-01",
            title="Alpen",
            description=None,
            file_path="cycling/alpen.mp4",
            duration_seconds=None,
            active=True,
            created_at=datetime.now(UTC),
        )
    )
    video_repository.save(
        WorkoutVideo(
            id="cycling-kueste-01",
            title="Küste",
            description=None,
            file_path="cycling/kueste.mp4",
            duration_seconds=None,
            active=True,
            created_at=datetime.now(UTC),
        )
    )

    service = WorkoutService(
        repository=workout_repository,
        video_repository=video_repository,
    )

    first_workout = service.start(
        person_id=1,
        recommendation=RECOMMENDATION,
        video_id="cycling-alpen-01",
    )

    service.checkpoint(
        first_workout.id,
        elapsed_seconds=60,
        distance_m=500,
        video_position_seconds=87.5,
    )

    second_workout = service.start(
        person_id=1,
        recommendation=RECOMMENDATION,
        video_id="cycling-kueste-01",
    )

    assert second_workout.video_id == "cycling-kueste-01"
    assert second_workout.video_position_seconds == 0.0


def test_start_rejects_inactive_selected_video() -> None:
    workout_repository = InMemoryWorkoutRepository()
    video_repository = InMemoryWorkoutVideoRepository()

    video_repository.save(
        WorkoutVideo(
            id="cycling-old-01",
            title="Altes Video",
            description=None,
            file_path="cycling/old.mp4",
            duration_seconds=None,
            active=False,
            created_at=datetime.now(UTC),
        )
    )

    service = WorkoutService(
        repository=workout_repository,
        video_repository=video_repository,
    )

    with pytest.raises(
        InvalidWorkoutVideoError,
        match="Workout video is not available: cycling-old-01",
    ):
        service.start(
            person_id=1,
            recommendation=RECOMMENDATION,
            video_id="cycling-old-01",
        )


def test_start_rejects_unknown_selected_video() -> None:
    service = WorkoutService(
        repository=InMemoryWorkoutRepository(),
        video_repository=InMemoryWorkoutVideoRepository(),
    )

    with pytest.raises(
        InvalidWorkoutVideoError,
        match="Workout video is not available: missing-video",
    ):
        service.start(
            person_id=1,
            recommendation=RECOMMENDATION,
            video_id="missing-video",
        )