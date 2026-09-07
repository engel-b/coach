from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class StartWorkoutRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    video_id: str | None = Field(
        default=None,
        alias="videoId",
        min_length=1,
    )


class WorkoutPhaseResponse(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    phase_type: str
    duration_minutes: int
    target_heart_rate_min: int
    target_heart_rate_max: int


class WorkoutCheckpointRequest(BaseModel):
    elapsed_seconds: int = Field(
        ge=0,
        validation_alias="elapsedSeconds",
        serialization_alias="elapsedSeconds",
    )
    distance_m: int = Field(
        ge=0,
        validation_alias="distanceM",
        serialization_alias="distanceM",
    )
    video_position_seconds: float = Field(
        ge=0,
        validation_alias="videoPositionSeconds",
        serialization_alias="videoPositionSeconds",
    )

    model_config = ConfigDict(
        populate_by_name=True,
    )


class FinishWorkoutRequest(BaseModel):
    """
    Request für regulären Abschluss oder Abbruch eines Workouts.

    elapsed_seconds ist die tatsächlich absolvierte aktive Trainingszeit.

    distance_m ist die während dieses Workouts gefahrene Distanz
    in ganzen Metern.
    """

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    elapsed_seconds: Annotated[
        int,
        Field(ge=0),
    ]

    distance_m: Annotated[
        int,
        Field(ge=0),
    ]


class WorkoutResponse(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    id: str
    person_id: int
    started_at: datetime
    status: str
    total_duration_minutes: int
    elapsed_seconds: int
    distance_m: int

    video_id: str
    video_position_seconds: float

    completed_at: datetime | None
    phases: list[WorkoutPhaseResponse]


class WorkoutSummaryResponse(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    planned_seconds: int
    elapsed_seconds: int
    distance_m: int
    completion_percent: int
    status: str
