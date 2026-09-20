from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

import apps.api.main as api_main
import apps.api.wiring as api_wiring
from features.workout.domain.video import WorkoutVideo
from features.workout.persistence.in_memory_workout_video_repository import (
    InMemoryWorkoutVideoRepository,
)
from features.workout.service.video_catalog_service import VideoCatalogService

client = TestClient(api_main.app)


@pytest.fixture(autouse=True)
def isolated_video_catalog(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository = InMemoryWorkoutVideoRepository()

    repository.save(
        WorkoutVideo(
            id="Lqhq5UQ-U8A",
            title="Alpen",
            description="Trainingsvideo Alpen",
            file_path="cycling/alpen.mp4",
            duration_seconds=3600.0,
            active=True,
            created_at=datetime.now(UTC),
        )
    )

    repository.save(
        WorkoutVideo(
            id="inactive-video",
            title="Inaktives Video",
            description=None,
            file_path="cycling/inactive.mp4",
            duration_seconds=None,
            active=False,
            created_at=datetime.now(UTC),
        )
    )

    monkeypatch.setattr(
        api_wiring,
        "video_catalog_service",
        VideoCatalogService(repository=repository),
    )


def test_get_workout_videos_returns_only_active_videos() -> None:
    response = client.get("/api/workout-videos")

    assert response.status_code == 200

    body = response.json()

    assert len(body) == 1
    assert body[0] == {
        "id": "Lqhq5UQ-U8A",
        "title": "Alpen",
        "description": "Trainingsvideo Alpen",
        "url": "/videos/cycling/alpen.mp4",
        "durationSeconds": 3600.0,
        "active": True,
    }


def test_get_workout_video_by_id() -> None:
    response = client.get("/api/workout-videos/Lqhq5UQ-U8A")

    assert response.status_code == 200

    body = response.json()

    assert body["id"] == "Lqhq5UQ-U8A"
    assert body["url"] == "/videos/cycling/alpen.mp4"


def test_unknown_workout_video_returns_404() -> None:
    response = client.get("/api/workout-videos/does-not-exist")

    assert response.status_code == 404
