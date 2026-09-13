from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

from features.workout.domain.runtime import WorkoutRuntimeState


class StartWorkoutRequest(BaseModel):
    """Optionale Auswahl eines Trainingsvideos beim Start."""

    model_config = ConfigDict(populate_by_name=True)

    video_id: str | None = Field(
        default=None,
        alias="videoId",
        min_length=1,
        description=(
            "Stabile ID des gewünschten Videos. Ohne Angabe wird die "
            "letzte Videoauswahl fortgesetzt oder das Standardvideo verwendet."
        ),
        examples=["Lqhq5UQ-U8A"],
    )


class WorkoutPhaseResponse(BaseModel):
    """Eine Phase der gespeicherten Trainingseinheit."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    phase_type: str = Field(
        description="Fachlicher Typ der Trainingsphase.",
        examples=["warmup"],
    )
    duration_minutes: int = Field(
        description="Geplante Dauer der Phase in Minuten.",
        examples=[5],
    )
    target_heart_rate_min: int = Field(
        description="Untere Grenze des Zielpulsbereichs in Schlägen pro Minute.",
        examples=[110],
    )
    target_heart_rate_max: int = Field(
        description="Obere Grenze des Zielpulsbereichs in Schlägen pro Minute.",
        examples=[130],
    )


class WorkoutCheckpointRequest(BaseModel):
    """Zwischenstand eines laufenden Workouts."""

    elapsed_seconds: int = Field(
        ge=0,
        validation_alias="elapsedSeconds",
        serialization_alias="elapsedSeconds",
        description="Bisher absolvierte aktive Trainingszeit in Sekunden.",
        examples=[600],
    )
    distance_m: int = Field(
        ge=0,
        validation_alias="distanceM",
        serialization_alias="distanceM",
        description="Bisher gefahrene Distanz in ganzen Metern.",
        examples=[3500],
    )
    video_position_seconds: float = Field(
        ge=0,
        validation_alias="videoPositionSeconds",
        serialization_alias="videoPositionSeconds",
        description="Aktuelle Wiedergabeposition des Videos in Sekunden.",
        examples=[612.5],
    )
    runtime_state: WorkoutRuntimeState = Field(
        default=WorkoutRuntimeState.RUNNING,
        validation_alias="runtimeState",
        serialization_alias="runtimeState",
        description="Aktueller nicht persistierter Laufzeitzustand des Workouts.",
    )

    model_config = ConfigDict(
        populate_by_name=True,
    )


class WorkoutRuntimeStateRequest(BaseModel):
    """Sofortige Meldung eines Runtime-State-Wechsels an den Live Coach."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    runtime_state: WorkoutRuntimeState


class FinishWorkoutRequest(BaseModel):
    """
    Request zum Beenden eines Workouts.

    Der endgültige Workout-Status wird serverseitig aus der
    tatsächlich absolvierten Trainingszeit und der geplanten
    Trainingsdauer bestimmt.

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
        Field(
            ge=0,
            description="Tatsächlich absolvierte aktive Trainingszeit in Sekunden.",
            examples=[1800],
        ),
    ]

    distance_m: Annotated[
        int,
        Field(
            ge=0,
            description="Während dieses Workouts gefahrene Distanz in ganzen Metern.",
            examples=[10500],
        ),
    ]


class WorkoutResponse(BaseModel):
    """Gespeicherte Trainingseinheit einschließlich Phasen und Videostand."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    id: str = Field(
        description="Eindeutige ID des Workouts.",
        examples=["workout-123"],
    )
    person_id: int = Field(
        description="Stabile numerische ID der trainierenden Person.",
        examples=[1],
    )
    started_at: datetime = Field(
        description="Zeitpunkt, zu dem das Workout gestartet wurde.",
        examples=["2026-09-08T09:00:00Z"],
    )
    status: str = Field(
        description="Persistierter Status der Trainingseinheit.",
        examples=["running"],
    )
    total_duration_minutes: int = Field(
        description="Geplante Gesamtdauer in Minuten.",
        examples=[45],
    )
    elapsed_seconds: int = Field(
        description="Bisher absolvierte aktive Trainingszeit in Sekunden.",
        examples=[600],
    )
    distance_m: int = Field(
        description="Bisher gefahrene Distanz in ganzen Metern.",
        examples=[3500],
    )
    video_id: str = Field(
        description="Stabile ID des für das Workout ausgewählten Videos.",
        examples=["Lqhq5UQ-U8A"],
    )
    video_position_seconds: float = Field(
        description="Zuletzt gespeicherte Wiedergabeposition in Sekunden.",
        examples=[612.5],
    )
    completed_at: datetime | None = Field(
        description="Zeitpunkt der Beendigung oder null bei einem laufenden Workout.",
        examples=["2026-09-08T09:45:00Z"],
    )
    phases: list[WorkoutPhaseResponse] = Field(
        description="Geordnete Trainingsphasen mit Dauer und Zielpulsbereichen.",
    )


class WorkoutSummaryResponse(BaseModel):
    """Zusammenfassung der geplanten und absolvierten Trainingsleistung."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    planned_seconds: int = Field(
        description="Geplante Trainingsdauer in Sekunden.",
        examples=[2700],
    )
    elapsed_seconds: int = Field(
        description="Tatsächlich absolvierte aktive Trainingszeit in Sekunden.",
        examples=[1800],
    )
    distance_m: int = Field(
        description="Während des Workouts gefahrene Distanz in ganzen Metern.",
        examples=[10500],
    )
    completion_percent: int = Field(
        description="Erfüllungsgrad der geplanten Trainingsdauer in Prozent.",
        examples=[67],
    )
    status: str = Field(
        description="Persistierter Status des Workouts.",
        examples=["completed"],
    )
