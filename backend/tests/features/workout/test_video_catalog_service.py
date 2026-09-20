from datetime import UTC, datetime, timedelta

from features.training.domain.recommendation import WorkoutPhase, WorkoutPhaseType
from features.workout.domain.session import WorkoutSession, WorkoutStatus
from features.workout.domain.video import WorkoutVideo
from features.workout.persistence.in_memory_workout_repository import InMemoryWorkoutRepository
from features.workout.persistence.in_memory_workout_video_repository import (
    InMemoryWorkoutVideoRepository,
)
from features.workout.service.video_catalog_service import VideoCatalogService

PHASES = (
    WorkoutPhase(
        phase_type=WorkoutPhaseType.MAIN,
        duration_minutes=20,
        target_heart_rate_min=100,
        target_heart_rate_max=120,
    ),
)


def _workout(
    identifier: str, person_id: int, video_id: str, started_at: datetime
) -> WorkoutSession:
    return WorkoutSession(
        id=identifier,
        person_id=person_id,
        started_at=started_at,
        status=WorkoutStatus.COMPLETED,
        phases=PHASES,
        total_duration_minutes=20,
        video_id=video_id,
    )


def test_person_video_list_is_sorted_by_usage_and_marks_last_video() -> None:
    videos = InMemoryWorkoutVideoRepository()
    workouts = InMemoryWorkoutRepository()
    now = datetime.now(UTC)
    for video_id, title in (("new", "New"), ("rare", "Rare"), ("often", "Often")):
        videos.save(
            WorkoutVideo(id=video_id, title=title, file_path=f"{video_id}.mp4", created_at=now)
        )
    workouts.save(_workout("1", 7, "often", now - timedelta(days=3)))
    workouts.save(_workout("2", 7, "often", now - timedelta(days=2)))
    workouts.save(_workout("3", 7, "rare", now - timedelta(days=1)))

    result = VideoCatalogService(videos, workouts).get_for_person(7)

    assert [item.video.id for item in result] == ["new", "rare", "often"]
    assert result[0].is_new is True
    assert result[1].is_last_used is True
    assert result[2].usage_count == 2
