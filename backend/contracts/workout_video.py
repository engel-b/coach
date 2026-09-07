from pydantic import BaseModel, ConfigDict, Field

from domains.workout.video import WorkoutVideo


class WorkoutVideoResponse(BaseModel):
    id: str
    title: str
    description: str | None
    url: str
    duration_seconds: float | None = Field(
        serialization_alias="durationSeconds",
    )

    model_config = ConfigDict(
        populate_by_name=True,
    )


def to_workout_video_response(
    video: WorkoutVideo,
) -> WorkoutVideoResponse:
    return WorkoutVideoResponse(
        id=video.id,
        title=video.title,
        description=video.description,
        url=f"/videos/{video.file_path}",
        duration_seconds=video.duration_seconds,
    )