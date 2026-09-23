from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class CheckInRequest(BaseModel):
    """Aktuelle Tagesform und verfügbare Trainingszeit einer Person."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    energy: int = Field(
        description="Selbsteinschätzung des aktuellen Energielevels.",
        examples=[7],
    )
    recovery: int = Field(
        description="Selbsteinschätzung der körperlichen Erholung.",
        examples=[8],
    )
    muscle_soreness: int = Field(
        description="Selbsteinschätzung des aktuellen Muskelkaters.",
        examples=[2],
    )
    stress: int = Field(
        description="Selbsteinschätzung des aktuellen Stresslevels.",
        examples=[3],
    )
    available_training_minutes: int = Field(
        description="Heute verfügbare Trainingszeit in Minuten.",
        examples=[45],
    )
    current_weight_kg: float | None = Field(
        default=None,
        gt=0,
        le=500,
        description="Optional gemessenes aktuelles Körpergewicht in Kilogramm.",
        examples=[82.4],
    )
    sleep_hours: float | None = Field(
        default=None,
        ge=0,
        le=24,
        description="Optional erfasste Schlafdauer in Stunden.",
        examples=[7.5],
    )
    steps: int | None = Field(
        default=None,
        ge=0,
        description="Optional erfasste Schrittzahl.",
        examples=[8450],
    )
    resting_heart_rate_bpm: int | None = Field(
        default=None,
        ge=35,
        le=120,
        description=(
            "Optional heute in Ruhe gemessene Herzfrequenz. Der Wert kann "
            "ueber mehrere Check-ins zur persoenlichen Ruhepuls-Baseline beitragen."
        ),
        examples=[72],
    )


class CheckInResponse(BaseModel):
    """Gespeicherter Check-in einschließlich Person und Zeitstempel."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    person_id: int = Field(
        description="Stabile numerische ID der zugehörigen Person.",
        examples=[1],
    )
    timestamp: datetime = Field(
        description="Zeitpunkt, zu dem der Check-in erfasst wurde.",
        examples=["2026-09-08T08:30:00Z"],
    )

    energy: int = Field(
        description="Erfasstes Energielevel.",
        examples=[7],
    )
    recovery: int = Field(
        description="Erfasste körperliche Erholung.",
        examples=[8],
    )
    muscle_soreness: int = Field(
        description="Erfasster Muskelkater.",
        examples=[2],
    )
    stress: int = Field(
        description="Erfasstes Stresslevel.",
        examples=[3],
    )
    available_training_minutes: int = Field(
        description="Verfügbare Trainingszeit in Minuten.",
        examples=[45],
    )
    current_weight_kg: float | None = Field(
        default=None,
        gt=0,
        le=500,
        description="Optional gemessenes aktuelles Körpergewicht in Kilogramm.",
        examples=[82.4],
    )
    sleep_hours: float | None = Field(
        default=None,
        ge=0,
        le=24,
        description="Optional erfasste Schlafdauer in Stunden.",
        examples=[7.5],
    )
    steps: int | None = Field(
        default=None,
        ge=0,
        description="Optional erfasste Schrittzahl.",
        examples=[8450],
    )
    resting_heart_rate_bpm: int | None = Field(
        default=None,
        ge=35,
        le=120,
        description="Optional im Check-in erfasster Ruhepuls.",
        examples=[72],
    )
