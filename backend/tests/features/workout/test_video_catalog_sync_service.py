from datetime import UTC, datetime
from pathlib import Path

from features.workout.domain.video import WorkoutVideo
from features.workout.persistence.in_memory_workout_video_repository import (
    InMemoryWorkoutVideoRepository,
)
from features.workout.service.video_catalog_sync_service import VideoCatalogSyncService


def test_sync_adds_new_and_deactivates_missing_video(tmp_path: Path) -> None:
    repository = InMemoryWorkoutVideoRepository()
    repository.save(
        WorkoutVideo(id="old", title="Old", file_path="old.mp4", created_at=datetime.now(UTC))
    )
    (tmp_path / "cycling").mkdir()
    (tmp_path / "cycling" / "forest_ride.mp4").write_bytes(b"video")

    result = VideoCatalogSyncService(repository=repository, video_directory=tmp_path).sync()

    assert result.added == 1
    assert result.deactivated == 1
    assert repository.get("old") is not None
    assert repository.get("old").active is False  # type: ignore[union-attr]
    new_video = repository.get_by_file_path("cycling/forest_ride.mp4")
    assert new_video is not None
    assert new_video.active is True
    assert new_video.title == "Forest Ride"


def test_sync_does_not_deactivate_when_root_is_missing(tmp_path: Path) -> None:
    repository = InMemoryWorkoutVideoRepository()
    repository.save(
        WorkoutVideo(id="known", title="Known", file_path="known.mp4", created_at=datetime.now(UTC))
    )

    result = VideoCatalogSyncService(
        repository=repository, video_directory=tmp_path / "missing"
    ).sync()

    assert result.deactivated == 0
    assert repository.get("known").active is True  # type: ignore[union-attr]
