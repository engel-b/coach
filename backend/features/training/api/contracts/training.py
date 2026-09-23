from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class WorkoutPhaseResponse(BaseModel):
    """Eine Phase der empfohlenen Trainingseinheit."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    phase_type: str = Field(
        description="Fachlicher Typ der Trainingsphase.",
        examples=["warmup"],
    )
    duration_minutes: int = Field(
        description="Geplante Dauer dieser Phase in Minuten.",
        examples=[5],
    )
    target_heart_rate_min: int = Field(
        description=("Untere Grenze des empfohlenen Zielpulsbereichs in Schlägen pro Minute."),
        examples=[110],
    )
    target_heart_rate_max: int = Field(
        description=("Obere Grenze des empfohlenen Zielpulsbereichs in Schlägen pro Minute."),
        examples=[130],
    )


class WeightGoalProgressResponse(BaseModel):
    """Deskriptiver Fortschritt zum hinterlegten Gewichts-Ziel."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    status: str
    start_weight_kg: float | None = None
    current_weight_kg: float | None = None
    target_weight_kg: float | None = None
    remaining_kg: float | None = None
    lost_since_start_kg: float | None = None
    progress_percent: float | None = None


class HeartRateTargetBasisResponse(BaseModel):
    """Nachvollziehbare Grundlage der berechneten Zielpulsbereiche."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    method: str = Field(
        description="Berechnungsmethode für die Zielpulsbereiche.",
        examples=["heart_rate_reserve"],
    )
    max_heart_rate_bpm: int = Field(
        description="Für die Berechnung verwendete maximale Herzfrequenz.",
        examples=[180],
    )
    resting_heart_rate_bpm: int | None = Field(
        default=None,
        description="Im Profil hinterlegter Ruhepuls, sofern vorhanden.",
        examples=[72],
    )
    reference_resting_heart_rate_bpm: int | None = Field(
        default=None,
        description=(
            "Konservativ begrenzter Ruhepuls-Referenzwert, der bei der "
            "Herzfrequenzreserve tatsächlich verwendet wurde."
        ),
        examples=[72],
    )
    resting_heart_rate_source: str | None = Field(
        default=None,
        description="Quelle des verwendeten Ruhepulswerts.",
        examples=["check_in_baseline"],
    )
    resting_heart_rate_sample_count: int = Field(
        default=0,
        ge=0,
        description="Anzahl der Check-in-Messungen hinter einer ermittelten Baseline.",
        examples=[5],
    )


class TrainingRecommendationResponse(BaseModel):
    """Individuelle Empfehlung für eine Trainingseinheit."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    workout_type: str = Field(
        description="Fachlicher Typ des empfohlenen Workouts.",
        examples=["endurance"],
    )
    total_duration_minutes: int = Field(
        description="Geplante Gesamtdauer des Workouts in Minuten.",
        examples=[45],
    )
    reason: str = Field(
        description="Fachliche Begründung für die Empfehlung.",
        examples=["Die aktuelle Tagesform eignet sich für eine moderate Trainingseinheit."],
    )
    heart_rate_target_basis: HeartRateTargetBasisResponse = Field(
        description="Grundlage der Zielpulsberechnung für diese Empfehlung.",
    )
    weight_goal_progress: WeightGoalProgressResponse | None = Field(
        default=None,
        description=(
            "Strukturierter Fortschritt zum Gewichts-Ziel, sofern für die Empfehlung relevant."
        ),
    )
    reason_codes: list[str] = Field(
        default_factory=list,
        description=(
            "Strukturierte, stabile Begründungscodes für UI, Tests und spätere LLM-Nutzung."
        ),
        examples=[["readiness_good", "weight_loss_goal", "weight_trend_down"]],
    )
    phases: list[WorkoutPhaseResponse] = Field(
        description=("Geordnete Trainingsphasen mit Dauer und Zielpulsbereich."),
    )
