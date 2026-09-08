from fastapi import APIRouter, HTTPException

from application.workout.video_catalog_service import (
    WorkoutVideoNotFoundError,
)
from apps.api import wiring
from contracts.workout_video import (
    WorkoutVideoResponse,
    to_workout_video_response,
)

router = APIRouter()


@router.get(
    "/api/workout-videos",
    response_model=list[WorkoutVideoResponse],
    response_model_by_alias=True,
)
async def get_workout_videos() -> list[WorkoutVideoResponse]:
    videos = wiring.video_catalog_service.get_available()

    return [to_workout_video_response(video) for video in videos]


@router.get(
    "/api/workout-videos/{video_id}",
    response_model=WorkoutVideoResponse,
    response_model_by_alias=True,
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
