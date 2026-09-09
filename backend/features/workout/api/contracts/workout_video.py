from pydantic import BaseModel, ConfigDict, Field

from features.workout.domain.video import WorkoutVideo
from features.workout.domain.video_path import validate_workout_video_path


class WorkoutVideoResponse(BaseModel):
    """Metadaten eines Trainingsvideos aus dem Katalog."""

    id: str = Field(
        description="Stabile ID des Videos, unabhängig vom Dateinamen.",
        examples=["Lqhq5UQ-U8A"],
    )
    title: str = Field(
        description="Anzeigename des Trainingsvideos.",
        examples=["Alpen"],
    )
    description: str | None = Field(
        description="Optionale Beschreibung des Videos.",
        examples=["Eine virtuelle Radtour durch die Alpen."],
    )
    url: str = Field(
        description="Relative URL zur MP4-Datei des Trainingsvideos.",
        examples=["/videos/cycling/alpen.mp4"],
    )
    duration_seconds: float | None = Field(
        serialization_alias="durationSeconds",
        description="Optionale Gesamtdauer des Videos in Sekunden.",
        examples=[3600.0],
    )

    model_config = ConfigDict(
        populate_by_name=True,
    )


def to_workout_video_response(
    video: WorkoutVideo,
) -> WorkoutVideoResponse:
    file_path = validate_workout_video_path(video.file_path)

    return WorkoutVideoResponse(
        id=video.id,
        title=video.title,
        description=video.description,
        url=f"/videos/{file_path}",
        duration_seconds=video.duration_seconds,
    )
