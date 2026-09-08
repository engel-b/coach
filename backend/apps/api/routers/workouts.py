from fastapi import APIRouter, HTTPException

from application.workout.service import (
    InvalidWorkoutDurationError,
    InvalidWorkoutVideoError,
    WorkoutAlreadyFinishedError,
    WorkoutNotFoundError,
)
from apps.api import wiring
from apps.api.recommendation import create_training_recommendation
from contracts.workout import (
    FinishWorkoutRequest,
    StartWorkoutRequest,
    WorkoutCheckpointRequest,
    WorkoutResponse,
    WorkoutSummaryResponse,
)
from contracts.workout_mapper import (
    to_workout_response,
    to_workout_summary_response,
)

router = APIRouter()


@router.get(
    "/api/persons/{person_id}/workouts",
    response_model=list[WorkoutResponse],
    response_model_by_alias=True,
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
