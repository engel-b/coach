from typing import Annotated

from fastapi import APIRouter, HTTPException, Path

from apps.api import wiring
from features.training.api.recommendation import create_training_recommendation
from features.workout.api.contracts.workout import (
    FinishWorkoutRequest,
    StartWorkoutRequest,
    WorkoutCheckpointRequest,
    WorkoutResponse,
    WorkoutSummaryResponse,
)
from features.workout.api.contracts.workout_mapper import (
    to_workout_response,
    to_workout_summary_response,
)
from features.workout.service.service import (
    InvalidWorkoutDurationError,
    InvalidWorkoutVideoError,
    WorkoutAlreadyFinishedError,
    WorkoutNotFoundError,
)

router = APIRouter(tags=["Workouts"])


PersonId = Annotated[
    int,
    Path(
        title="Personen-ID",
        description="Stabile numerische ID der Person.",
    ),
]

WorkoutId = Annotated[
    str,
    Path(
        title="Workout-ID",
        description="Eindeutige ID der gespeicherten Trainingseinheit.",
    ),
]


@router.get(
    "/api/persons/{person_id}/workouts",
    response_model=list[WorkoutResponse],
    response_model_by_alias=True,
    summary="Trainingshistorie abrufen",
    description=(
        "Liefert die gespeicherten Workouts einer Person. Die Anzahl "
        "kann über den Parameter limit auf 1 bis 100 Einträge begrenzt "
        "werden. Ohne Angabe werden höchstens 20 Einträge geliefert."
    ),
    responses={
        404: {"description": "Die Person wurde nicht gefunden."},
        422: {"description": "Der Parameter limit liegt außerhalb des erlaubten Bereichs."},
    },
)
async def workout_history(
    person_id: int,
    limit: int = 20,
) -> list[WorkoutResponse]:
    person = wiring.person_service.get_person(person_id)

    if person is None:
        raise HTTPException(
            status_code=404,
            detail="Person not found",
        )

    if limit < 1 or limit > 100:
        raise HTTPException(
            status_code=422,
            detail="Limit must be between 1 and 100",
        )

    workouts = wiring.workout_service.get_for_person(
        person_id,
        limit=limit,
    )

    return [to_workout_response(workout) for workout in workouts]


@router.post(
    "/api/persons/{person_id}/workouts",
    response_model=WorkoutResponse,
    response_model_by_alias=True,
    summary="Workout starten",
    description=(
        "Erstellt eine neue Trainingseinheit auf Basis der aktuellen "
        "Trainingsempfehlung. Dafür müssen ein Personenprofil und ein "
        "Check-in vorhanden sein.\n\n"
        "Der Request-Body ist optional. Ohne explizite Videoauswahl wird "
        "das zuletzt verwendete Video der Person mit seiner gespeicherten "
        "Position fortgesetzt oder das Standardvideo verwendet. Wird "
        "ein anderes Video ausgewählt, beginnt dieses bei Position 0."
    ),
    responses={
        404: {"description": "Die Person oder ihr Profil wurde nicht gefunden."},
        409: {"description": "Es liegt noch kein Check-in für die Person vor."},
        422: {"description": "Die ausgewählte Video-ID ist ungültig oder nicht verfügbar."},
    },
)
async def start_workout(
    person_id: int,
    request: StartWorkoutRequest | None = None,
) -> WorkoutResponse:
    person = wiring.person_service.get_person(person_id)

    if person is None:
        raise HTTPException(
            status_code=404,
            detail="Person not found",
        )

    recommendation = create_training_recommendation(person_id)

    try:
        workout = wiring.workout_service.start(
            person_id=person_id,
            recommendation=recommendation,
            video_id=(request.video_id if request is not None else None),
        )
    except InvalidWorkoutVideoError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    return to_workout_response(workout)


@router.post(
    "/api/workouts/{workout_id}/checkpoint",
    response_model=WorkoutResponse,
    response_model_by_alias=True,
    summary="Workout-Zwischenstand speichern",
    description=(
        "Speichert die absolvierte aktive Trainingszeit, die gefahrene "
        "Distanz und die aktuelle Videoposition. Checkpoints sind nur "
        "für laufende Workouts zulässig. Die gespeicherte Videoposition "
        "wird für die spätere Fortsetzung verwendet."
    ),
    responses={
        404: {"description": "Das Workout wurde nicht gefunden."},
        409: {"description": "Das Workout ist bereits abgeschlossen oder abgebrochen."},
        422: {"description": "Die übermittelten Zwischenstandswerte sind ungültig."},
    },
)
async def checkpoint_workout(
    workout_id: str,
    request: WorkoutCheckpointRequest,
) -> WorkoutResponse:
    try:
        workout = wiring.workout_service.checkpoint(
            workout_id,
            elapsed_seconds=request.elapsed_seconds,
            distance_m=request.distance_m,
            video_position_seconds=(request.video_position_seconds),
        )
    except WorkoutNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc
    except WorkoutAlreadyFinishedError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc
    except InvalidWorkoutDurationError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    return to_workout_response(workout)


@router.post(
    "/api/workouts/{workout_id}/complete",
    response_model=WorkoutResponse,
    response_model_by_alias=True,
    summary="Workout regulär abschließen",
    description=(
        "Markiert ein laufendes Workout als abgeschlossen und speichert "
        "die tatsächlich absolvierte Trainingszeit sowie die Distanz. "
        "Die Videoposition wird aus dem zuletzt gespeicherten Checkpoint "
        "übernommen."
    ),
    responses={
        404: {"description": "Das Workout wurde nicht gefunden."},
        409: {"description": "Das Workout wurde bereits beendet."},
        422: {"description": "Die übermittelten Abschlusswerte sind ungültig."},
    },
)
async def complete_workout(
    workout_id: str,
    request: FinishWorkoutRequest,
) -> WorkoutResponse:
    try:
        workout = wiring.workout_service.complete(
            workout_id,
            elapsed_seconds=request.elapsed_seconds,
            distance_m=request.distance_m,
        )
    except WorkoutNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc
    except WorkoutAlreadyFinishedError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc
    except InvalidWorkoutDurationError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    return to_workout_response(workout)


@router.post(
    "/api/workouts/{workout_id}/abort",
    response_model=WorkoutResponse,
    response_model_by_alias=True,
    summary="Workout abbrechen",
    description=(
        "Beendet ein Workout vorzeitig und speichert die bis dahin "
        "absolvierte Trainingszeit und Distanz. Ein abgebrochenes "
        "Workout bleibt in der Trainingshistorie erhalten."
    ),
    responses={
        404: {"description": "Das Workout wurde nicht gefunden."},
        409: {"description": "Das Workout wurde bereits beendet."},
        422: {"description": "Die übermittelten Abschlusswerte sind ungültig."},
    },
)
async def abort_workout(
    workout_id: str,
    request: FinishWorkoutRequest,
) -> WorkoutResponse:
    try:
        workout = wiring.workout_service.abort(
            workout_id,
            elapsed_seconds=request.elapsed_seconds,
            distance_m=request.distance_m,
        )
    except WorkoutNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc
    except WorkoutAlreadyFinishedError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc
    except InvalidWorkoutDurationError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    return to_workout_response(workout)


@router.get(
    "/api/workouts/{workout_id}/summary",
    response_model=WorkoutSummaryResponse,
    response_model_by_alias=True,
    summary="Workout-Zusammenfassung abrufen",
    description=(
        "Liefert die geplante und tatsächlich absolvierte Trainingszeit, "
        "die Distanz, den Erfüllungsgrad und den Status eines Workouts."
    ),
    responses={
        404: {"description": "Das Workout wurde nicht gefunden."},
    },
)
async def workout_summary(
    workout_id: str,
) -> WorkoutSummaryResponse:
    try:
        summary = wiring.workout_service.get_summary(workout_id)
    except WorkoutNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    return to_workout_summary_response(summary)
