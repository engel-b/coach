from datetime import UTC, date, datetime
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

import apps.api.main as api_main
import apps.api.wiring as api_wiring
from adapters.persistence.in_memory_check_in_repository import InMemoryCheckInRepository
from adapters.persistence.in_memory_workout_repository import InMemoryWorkoutRepository
from adapters.persistence.in_memory_workout_video_repository import InMemoryWorkoutVideoRepository
from application.check_in.service import CheckInService
from application.person.person_service import PersonService
from application.person.profile_service import PersonProfileService
from application.workout.service import WorkoutService
from domains.person.person import Person
from domains.person.profile import PersonProfile, TrainingGoal
from domains.workout.session import DEFAULT_VIDEO_ID
from domains.workout.video import WorkoutVideo

client = TestClient(api_main.app)


@pytest.fixture(autouse=True)
def isolated_workout_service(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Isoliert alle Persistenzzugriffe des Workout-API-Durchstichs."""

    person = Person(id=1, display_name="Person 1")

    profile = PersonProfile(
        person_id=1,
        date_of_birth=date(1980, 1, 1),
        height_cm=180,
        training_goal=TrainingGoal.GENERAL_FITNESS,
    )

    person_repository = Mock()

    def get_person(person_id: int) -> Person | None:
        if person_id == 1:
            return person
        return None

    person_repository.get.side_effect = get_person
    person_repository.get_all.return_value = [person]

    profile_repository = Mock()

    def get_profile(person_id: int) -> PersonProfile | None:
        if person_id == 1:
            return profile
        return None

    profile_repository.get.side_effect = get_profile

    monkeypatch.setattr(
        api_wiring,
        "person_service",
        PersonService(repository=person_repository),
    )
    monkeypatch.setattr(
        api_wiring,
        "person_profile_service",
        PersonProfileService(repository=profile_repository),
    )
    monkeypatch.setattr(
        api_wiring,
        "check_in_service",
        CheckInService(repository=InMemoryCheckInRepository()),
    )
    monkeypatch.setattr(
        api_wiring,
        "workout_service",
        WorkoutService(repository=InMemoryWorkoutRepository()),
    )


def create_check_in(
    person_id: int,
) -> None:
    """
    Erstellt den für eine Trainingsempfehlung notwendigen Check-in.

    Der Workout-Endpoint soll bewusst über die echte HTTP-API
    vorbereitet werden und nicht durch direkten Zugriff auf Services.
    """

    response = client.post(
        f"/api/persons/{person_id}/check-ins",
        json={
            "energy": 4,
            "recovery": 4,
            "muscleSoreness": 1,
            "stress": 2,
            "availableTrainingMinutes": 30,
        },
    )

    assert response.status_code == 200


def start_workout(
    person_id: int,
) -> dict[str, object]:
    """
    Startet ein Workout über die HTTP-API und liefert
    den JSON-Response für weitere Tests zurück.
    """

    create_check_in(person_id)

    response = client.post(
        f"/api/persons/{person_id}/workouts",
    )

    assert response.status_code == 200

    result: dict[str, object] = response.json()

    return result


def test_workout_checkpoint() -> None:
    """
    Startet ein Workout über die HTTP-API und liefert
    den JSON-Response für weitere Tests zurück.
    """

    workout = start_workout(1)

    workout_id = workout["id"]

    response = client.post(
        f"/api/workouts/{workout_id}/checkpoint",
        json={
            "elapsedSeconds": 120,
            "distanceM": 1350,
            "videoPositionSeconds": 87.5,
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["elapsedSeconds"] == 120
    assert body["distanceM"] == 1350
    assert body["videoPositionSeconds"] == 87.5


def test_workout_can_be_started_via_api() -> None:
    workout = start_workout(1)

    assert workout["personId"] == 1
    assert workout["status"] == "running"
    assert workout["elapsedSeconds"] == 0
    assert workout["distanceM"] == 0
    assert workout["videoId"] == DEFAULT_VIDEO_ID
    assert workout["videoPositionSeconds"] == 0.0
    assert workout["totalDurationMinutes"] == 30

    phases = workout["phases"]

    assert isinstance(phases, list)
    assert len(phases) > 0


def test_workout_can_be_completed_via_api() -> None:
    workout = start_workout(1)

    workout_id = workout["id"]

    assert isinstance(workout_id, str)

    response = client.post(
        f"/api/workouts/{workout_id}/complete",
        json={
            "elapsedSeconds": 1800,
            "distanceM": 12345,
        },
    )

    assert response.status_code == 200

    completed = response.json()

    assert completed["id"] == workout_id
    assert completed["status"] == "completed"
    assert completed["elapsedSeconds"] == 1800
    assert completed["distanceM"] == 12345
    assert completed["videoId"] == workout["videoId"]
    assert completed["videoPositionSeconds"] == 0.0

    assert completed["completedAt"] is not None


def test_workout_can_be_aborted_via_api() -> None:
    workout = start_workout(1)

    workout_id = workout["id"]

    assert isinstance(workout_id, str)

    response = client.post(
        f"/api/workouts/{workout_id}/abort",
        json={
            "elapsedSeconds": 723,
            "distanceM": 4321,
        },
    )

    assert response.status_code == 200

    aborted = response.json()

    assert aborted["id"] == workout_id
    assert aborted["status"] == "aborted"
    assert aborted["elapsedSeconds"] == 723
    assert aborted["distanceM"] == 4321
    assert aborted["videoId"] == workout["videoId"]
    assert aborted["videoPositionSeconds"] == 0.0

    assert aborted["completedAt"] is not None


def test_new_workout_resumes_video_position_via_api() -> None:
    first_workout = start_workout(1)

    first_workout_id = first_workout["id"]

    assert isinstance(first_workout_id, str)

    checkpoint_response = client.post(
        f"/api/workouts/{first_workout_id}/checkpoint",
        json={
            "elapsedSeconds": 120,
            "distanceM": 1350,
            "videoPositionSeconds": 87.5,
        },
    )

    assert checkpoint_response.status_code == 200

    second_workout = start_workout(1)

    assert second_workout["videoId"] == first_workout["videoId"]
    assert second_workout["videoPositionSeconds"] == 87.5


def test_unknown_workout_cannot_be_completed() -> None:
    response = client.post(
        "/api/workouts/does-not-exist/complete",
        json={
            "elapsedSeconds": 100,
            "distanceM": 500,
        },
    )

    assert response.status_code == 404


def test_negative_elapsed_seconds_are_rejected() -> None:
    workout = start_workout(1)

    workout_id = workout["id"]

    assert isinstance(workout_id, str)

    response = client.post(
        f"/api/workouts/{workout_id}/abort",
        json={
            "elapsedSeconds": -1,
            "distanceM": 1000,
        },
    )

    assert response.status_code == 422


def test_negative_distance_is_rejected() -> None:
    workout = start_workout(1)

    workout_id = workout["id"]

    assert isinstance(workout_id, str)

    response = client.post(
        f"/api/workouts/{workout_id}/complete",
        json={
            "elapsedSeconds": 100,
            "distanceM": -1,
        },
    )

    assert response.status_code == 422


def test_get_workout_history_returns_workouts_newest_first() -> None:
    first = start_workout(1)
    second = start_workout(1)

    response = client.get(
        "/api/persons/1/workouts",
    )

    assert response.status_code == 200

    body = response.json()

    assert len(body) >= 2

    assert body[0]["id"] == second["id"]
    assert body[1]["id"] == first["id"]


def test_get_workout_history_respects_limit() -> None:
    start_workout(1)
    start_workout(1)

    response = client.get(
        "/api/persons/1/workouts?limit=1",
    )

    assert response.status_code == 200

    body = response.json()

    assert len(body) == 1


def test_get_workout_history_for_unknown_person_returns_404() -> None:
    response = client.get(
        "/api/persons/999/workouts",
    )

    assert response.status_code == 404

    assert response.json() == {
        "detail": "Person not found",
    }


def test_get_workout_history_rejects_invalid_limit() -> None:
    response = client.get(
        "/api/persons/1/workouts?limit=0",
    )

    assert response.status_code == 422


def test_get_workout_summary() -> None:
    workout = start_workout(1)

    workout_id = workout["id"]

    assert isinstance(workout_id, str)

    complete_response = client.post(
        f"/api/workouts/{workout_id}/complete",
        json={
            "elapsedSeconds": 900,
            "distanceM": 6789,
        },
    )

    assert complete_response.status_code == 200

    response = client.get(f"/api/workouts/{workout_id}/summary")

    assert response.status_code == 200

    body = response.json()

    assert body["elapsedSeconds"] == 900
    assert body["distanceM"] == 6789
    assert body["status"] == "completed"

    # Die Empfehlung kann unterschiedliche Gesamtdauern
    # enthalten. Deshalb berechnen wir den erwarteten
    # Wert aus dem tatsächlich gestarteten Workout.
    total_duration_minutes = workout["totalDurationMinutes"]

    assert isinstance(
        total_duration_minutes,
        int,
    )

    expected_planned_seconds = total_duration_minutes * 60

    assert body["plannedSeconds"] == expected_planned_seconds

    assert body["completionPercent"] == round(900 / expected_planned_seconds * 100)


def test_get_workout_summary_for_unknown_workout_returns_404() -> None:
    response = client.get("/api/workouts/does-not-exist/summary")

    assert response.status_code == 404


def test_start_workout_with_selected_video(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workout_repository = InMemoryWorkoutRepository()
    video_repository = InMemoryWorkoutVideoRepository()

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

    monkeypatch.setattr(
        api_main,
        "workout_service",
        WorkoutService(
            repository=workout_repository,
            video_repository=video_repository,
        ),
    )

    create_check_in(1)

    response = client.post(
        "/api/persons/1/workouts",
        json={"videoId": "cycling-kueste-01"},
    )

    assert response.status_code == 200

    body = response.json()
    assert body["videoId"] == "cycling-kueste-01"
    assert body["videoPositionSeconds"] == 0.0


def test_start_workout_rejects_unknown_video(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        api_main,
        "workout_service",
        WorkoutService(
            repository=InMemoryWorkoutRepository(),
            video_repository=InMemoryWorkoutVideoRepository(),
        ),
    )

    create_check_in(1)

    response = client.post(
        "/api/persons/1/workouts",
        json={"videoId": "missing-video"},
    )

    assert response.status_code == 422
    assert response.json()["detail"] == ("Workout video is not available: missing-video")
