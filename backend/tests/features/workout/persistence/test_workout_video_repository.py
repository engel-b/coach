from datetime import UTC, datetime

from features.workout.domain.video import WorkoutVideo
from features.workout.persistence.sqlalchemy_workout_video_repository import (
    SqlAlchemyWorkoutVideoRepository,
)


def test_existing_workout_video_can_be_loaded() -> None:
    repository = SqlAlchemyWorkoutVideoRepository()

    video = repository.get("Lqhq5UQ-U8A")

    assert video is not None
    assert video.id == "Lqhq5UQ-U8A"
    assert video.title == "Italy Alps"
    assert video.file_path == "cycling/Lqhq5UQ-U8A.mp4"
    assert video.active is True


def test_workout_video_can_be_saved_and_loaded() -> None:
    repository = SqlAlchemyWorkoutVideoRepository()

    video = WorkoutVideo(
        id="test-video",
        title="Testvideo",
        description="Nur für den Repository-Test",
        file_path="cycling/test.mp4",
        duration_seconds=123.5,
        active=True,
        created_at=datetime.now(UTC),
    )

    repository.save(video)

    loaded = repository.get("test-video")

    assert loaded is not None
    assert loaded.id == "test-video"
    assert loaded.title == "Testvideo"
    assert loaded.description == "Nur für den Repository-Test"
    assert loaded.file_path == "cycling/test.mp4"
    assert loaded.duration_seconds == 123.5
    assert loaded.active is True
