import pytest
from fastapi.testclient import TestClient

import apps.api.main as api_main
from adapters.persistence.in_memory_workout_repository import InMemoryWorkoutRepository
from application.workout.service import WorkoutService
from domains.workout.session import DEFAULT_VIDEO_ID

client = TestClient(api_main.app)


@pytest.fixture(autouse=True)
def isolated_workout_service() -> None:
    """
    Jeder API-Test bekommt ein frisches Workout-Repository.

    Die HTTP-Routen selbst bleiben unverändert aktiv.
    Nur die Workout-Persistenz wird für den einzelnen Test
    durch eine isolierte InMemory-Instanz ersetzt.
    """
    repository = InMemoryWorkoutRepository()

    api_main.workout_service = WorkoutService(
        repository=repository,
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
