from typing import Annotated

from fastapi import APIRouter, HTTPException, Path, Query, Response, status

from apps.api import wiring
from features.workout.api.contracts.workout_video import (
    WorkoutVideoMutationRequest,
    WorkoutVideoResponse,
    WorkoutVideoSelectionResponse,
    to_workout_video_response,
    to_workout_video_selection_response,
)
from features.workout.service.video_catalog_service import (
    WorkoutVideoNotFoundError,
    WorkoutVideoPathConflictError,
)

router = APIRouter(tags=["Workout Videos"])


VideoId = Annotated[
    str,
    Path(
        title="Video-ID",
        description="Stabile ID eines Videos aus dem Trainingskatalog.",
    ),
]

PersonId = Annotated[
    int,
    Path(
        title="Person-ID",
        description="ID der Person, für die Trainingsvideos aufgelistet werden.",
        gt=0,
    ),
]

ActiveOnly = Annotated[
    bool,
    Query(
        alias="activeOnly",
        description="Gibt an, ob nur aktive Trainingsvideos zurückgegeben werden sollen.",
    ),
]


def _not_found(exc: WorkoutVideoNotFoundError) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.get(
    "/api/workout-videos",
    response_model=list[WorkoutVideoResponse],
    response_model_by_alias=True,
    summary="Verfügbare Trainingsvideos auflisten",
    description=(
        "Liefert die aktuell verfügbaren Trainingsvideos mit ihren "
        "Metadaten und der URL zur Videodatei. Die stabile Video-ID "
        "kann beim Start eines Workouts verwendet werden."
    ),
)
async def get_workout_videos(
    active_only: ActiveOnly = True,
) -> list[WorkoutVideoResponse]:
    videos = (
        wiring.video_catalog_service.get_available()
        if active_only
        else wiring.video_catalog_service.get_all()
    )
    return [to_workout_video_response(video) for video in videos]


@router.get(
    "/api/persons/{person_id}/workout-videos",
    response_model=list[WorkoutVideoSelectionResponse],
    response_model_by_alias=True,
    summary="Verfügbare Trainingsvideos sortiert nach Verwendung auflisten",
    description=(
        "Liefert die aktuell verfügbaren Trainingsvideos mit ihren "
        "Metadaten und der URL zur Videodatei. Die stabile Video-ID "
        "kann beim Start eines Workouts verwendet werden. "
        "Die Liste wird aufsteigend nach Verwendung sortiert."
    ),
)
async def get_workout_videos_for_person(
    person_id: PersonId,
) -> list[WorkoutVideoSelectionResponse]:
    return [
        to_workout_video_selection_response(item)
        for item in wiring.video_catalog_service.get_for_person(person_id)
    ]


@router.get(
    "/api/workout-videos/{video_id}",
    response_model=WorkoutVideoResponse,
    response_model_by_alias=True,
    summary="Trainingsvideo abrufen",
    description=(
        "Liefert die Metadaten eines Trainingsvideos anhand seiner "
        "stabilen ID. Die URL verweist auf die zugehörige MP4-Datei."
    ),
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Das Trainingsvideo wurde nicht gefunden."},
    },
)
async def get_workout_video(video_id: VideoId) -> WorkoutVideoResponse:
    try:
        return to_workout_video_response(wiring.video_catalog_service.get(video_id))
    except WorkoutVideoNotFoundError as exc:
        raise _not_found(exc) from exc


@router.post(
    "/api/workout-videos",
    response_model=WorkoutVideoResponse,
    response_model_by_alias=True,
    status_code=status.HTTP_201_CREATED,
)
async def create_workout_video(
    request: WorkoutVideoMutationRequest,
) -> WorkoutVideoResponse:
    try:
        video = wiring.video_catalog_service.create(
            title=request.title,
            description=request.description,
            file_path=request.file_path,
            duration_seconds=request.duration_seconds,
            active=request.active,
        )
    except WorkoutVideoPathConflictError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    return to_workout_video_response(video)


@router.put(
    "/api/workout-videos/{video_id}",
    response_model=WorkoutVideoResponse,
    response_model_by_alias=True,
)
async def update_workout_video(
    video_id: VideoId,
    request: WorkoutVideoMutationRequest,
) -> WorkoutVideoResponse:
    try:
        video = wiring.video_catalog_service.update(
            video_id,
            title=request.title,
            description=request.description,
            file_path=request.file_path,
            duration_seconds=request.duration_seconds,
            active=request.active,
        )
    except WorkoutVideoNotFoundError as exc:
        raise _not_found(exc) from exc
    except WorkoutVideoPathConflictError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    return to_workout_video_response(video)


@router.delete(
    "/api/workout-videos/{video_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_workout_video(video_id: VideoId) -> Response:
    try:
        wiring.video_catalog_service.deactivate(video_id)
    except WorkoutVideoNotFoundError as exc:
        raise _not_found(exc) from exc

    return Response(status_code=status.HTTP_204_NO_CONTENT)
