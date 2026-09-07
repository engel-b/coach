from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

import apps.api.main as api_main
from adapters.persistence.in_memory_workout_video_repository import (
    InMemoryWorkoutVideoRepository,
)
from application.workout.video_catalog_service import VideoCatalogService
from domains.workout.video import WorkoutVideo

client = TestClient(api_main.app)


@pytest.fixture(autouse=True)
def isolated_video_catalog(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository = InMemoryWorkoutVideoRepository()

    repository.save(
        WorkoutVideo(
            id="cycling-alpen-01",
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
        api_main,
        "video_catalog_service",
        VideoCatalogService(repository=repository),
    )


def test_get_workout_videos_returns_only_active_videos() -> None:
    response = client.get("/api/workout-videos")

    assert response.status_code == 200

    body = response.json()

    assert len(body) == 1
    assert body[0] == {
        "id": "cycling-alpen-01",
        "title": "Alpen",
        "description": "Trainingsvideo Alpen",
        "url": "/videos/cycling/alpen.mp4",
        "durationSeconds": 3600.0,
    }


def test_get_workout_video_by_id() -> None:
    response = client.get(
        "/api/workout-videos/cycling-alpen-01"
    )

    assert response.status_code == 200

    body = response.json()

    assert body["id"] == "cycling-alpen-01"
    assert body["url"] == "/videos/cycling/alpen.mp4"


def test_unknown_workout_video_returns_404() -> None:
    response = client.get(
        "/api/workout-videos/does-not-exist"
    )

    assert response.status_code == 404