from typing import Annotated

from fastapi import APIRouter, HTTPException, Path

from apps.api import wiring
from features.training.api.recommendation import create_training_recommendation
from features.workout.api.contracts.workout import (
    FinishWorkoutRequest,
    StartWorkoutRequest,
    WorkoutCheckpointRequest,
    WorkoutResponse,
    WorkoutRuntimeStateRequest,
    WorkoutSummaryResponse,
)
from features.workout.api.contracts.workout_mapper import (
    to_workout_response,
    to_workout_summary_response,
)
from features.workout.service.workout_service import (
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

    wiring.live_coaching_lifecycle.workout_started(workout)

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

    wiring.live_coaching_lifecycle.workout_checkpointed(
        workout,
        runtime_state=request.runtime_state,
    )

    return to_workout_response(workout)


@router.post(
    "/api/workouts/{workout_id}/runtime-state",
    status_code=204,
    summary="Workout-Laufzeitzustand melden",
    description=(
        "Meldet einen sofortigen Runtime-State-Wechsel an den Live Coach. "
        "Der Zustand wird nicht persistiert und beeinflusst das Workout selbst nicht."
    ),
)
async def update_workout_runtime_state(
    workout_id: str,
    request: WorkoutRuntimeStateRequest,
) -> None:
    workout = wiring.workout_service.get(workout_id)

    if workout is None:
        raise HTTPException(status_code=404, detail=f"Workout {workout_id} not found")

    if workout.status.value != "running":
        raise HTTPException(status_code=409, detail=f"Workout {workout_id} is not running")

    wiring.live_coaching_lifecycle.workout_runtime_state_changed(
        workout_id=workout_id,
        runtime_state=request.runtime_state,
    )


@router.post(
    "/api/workouts/{workout_id}/finish",
    response_model=WorkoutResponse,
    response_model_by_alias=True,
    summary="Workout beenden",
    description=(
        "Beendet ein laufendes Workout und speichert die tatsächlich "
        "absolvierte Trainingszeit sowie die Distanz. Das Backend bestimmt "
        "den fachlichen Endstatus anhand der absolvierten Trainingszeit. "
        "Wurde die geplante Trainingsdauer erreicht oder überschritten, "
        "wird das Workout als abgeschlossen gespeichert. Andernfalls "
        "wird es als abgebrochen gespeichert."
    ),
    responses={
        404: {"description": "Das Workout wurde nicht gefunden."},
        409: {"description": "Das Workout wurde bereits beendet."},
        422: {"description": "Die übermittelten Abschlusswerte sind ungültig."},
    },
)
async def finish_workout(
    workout_id: str,
    request: FinishWorkoutRequest,
) -> WorkoutResponse:
    heart_rate_summary = wiring.live_coaching_lifecycle.workout_heart_rate_summary(workout_id)

    bike_summary = wiring.live_coaching_lifecycle.workout_bike_summary(workout_id)

    try:
        workout = wiring.workout_service.finish(
            workout_id,
            elapsed_seconds=request.elapsed_seconds,
            distance_m=request.distance_m,
            heart_rate_summary=heart_rate_summary,
            bike_summary=bike_summary,
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

    wiring.live_coaching_lifecycle.workout_finished(workout)

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
