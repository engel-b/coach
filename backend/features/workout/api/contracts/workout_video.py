from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from features.workout.domain.video import WorkoutVideo
from features.workout.domain.video_path import validate_workout_video_path
from features.workout.service.video_catalog_service import WorkoutVideoSelection


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
    file_path: str = Field(
        serialization_alias="filePath",
        description=(
            "Relativer Pfad zur MP4-Datei innerhalb des konfigurierten Videoverzeichnisses."
        ),
        examples=["cycling/alpen.mp4"],
    )
    duration_seconds: float | None = Field(
        serialization_alias="durationSeconds",
        description="Optionale Gesamtdauer des Videos in Sekunden.",
        examples=[3600.0],
    )
    active: bool = Field(
        description="Gibt an, ob das Trainingsvideo aktuell verfügbar ist.",
        examples=[True],
    )
    model_config = ConfigDict(
        populate_by_name=True,
    )


class WorkoutVideoMutationRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = None
    file_path: str = Field(
        serialization_alias="filePath",
        validation_alias="filePath",
    )
    duration_seconds: float | None = Field(
        default=None,
        ge=0,
        serialization_alias="durationSeconds",
        validation_alias="durationSeconds",
    )
    active: bool = True
    model_config = ConfigDict(populate_by_name=True)


class WorkoutVideoSelectionResponse(WorkoutVideoResponse):
    usage_count: int = Field(serialization_alias="usageCount")
    is_new: bool = Field(serialization_alias="isNew")
    is_last_used: bool = Field(serialization_alias="isLastUsed")
    last_used_at: datetime | None = Field(serialization_alias="lastUsedAt")


def to_workout_video_response(video: WorkoutVideo) -> WorkoutVideoResponse:
    file_path = validate_workout_video_path(video.file_path)
    return WorkoutVideoResponse(
        id=video.id,
        title=video.title,
        description=video.description,
        file_path=file_path,
        duration_seconds=video.duration_seconds,
        active=video.active,
    )


def to_workout_video_selection_response(
    item: WorkoutVideoSelection,
) -> WorkoutVideoSelectionResponse:
    base = to_workout_video_response(item.video)
    return WorkoutVideoSelectionResponse(
        **base.model_dump(),
        usage_count=item.usage_count,
        is_new=item.is_new,
        is_last_used=item.is_last_used,
        last_used_at=item.last_used_at,
    )
