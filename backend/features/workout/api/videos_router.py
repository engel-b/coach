from typing import Annotated

from fastapi import APIRouter, HTTPException, Path

from apps.api import wiring
from features.workout.api.contracts.workout_video import (
    WorkoutVideoResponse,
    to_workout_video_response,
)
from features.workout.service.video_catalog_service import (
    WorkoutVideoNotFoundError,
)

router = APIRouter(tags=["Workout Videos"])


VideoId = Annotated[
    str,
    Path(
        title="Video-ID",
        description="Stabile ID eines Videos aus dem Trainingskatalog.",
    ),
]


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
async def get_workout_videos() -> list[WorkoutVideoResponse]:
    videos = wiring.video_catalog_service.get_available()

    return [to_workout_video_response(video) for video in videos]


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
        404: {"description": "Das Trainingsvideo wurde nicht gefunden."},
    },
)
async def get_workout_video(
    video_id: str,
) -> WorkoutVideoResponse:
    try:
        video = wiring.video_catalog_service.get(video_id)
    except WorkoutVideoNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    return to_workout_video_response(video)
