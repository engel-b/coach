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


class HeartRateHistoryResponse(BaseModel):
    """Verdichtete Herzfrequenz-Reaktion aus früheren Workouts."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    status: str
    workout_count: int = Field(ge=0)
    workout_type: str | None = Field(
        default=None,
        description="Workout-Typ, auf den diese historische Auswertung begrenzt wurde.",
    )
    median_in_target_percent: int | None = Field(default=None, ge=0, le=100)
    median_above_target_percent: int | None = Field(default=None, ge=0, le=100)
    median_below_target_percent: int | None = Field(default=None, ge=0, le=100)
    max_duration_minutes: int | None = Field(default=None, ge=1)
    response_trend: str = Field(
        default="insufficient_data",
        description=(
            "Deskriptiver Trend der mittleren Herzfrequenz relativ zum damals "
            "gültigen Zielbereich vergleichbarer Workouts."
        ),
    )
    median_target_position_percent: int | None = Field(
        default=None,
        description=(
            "Median der relativen Position der mittleren Herzfrequenz im damaligen "
            "Zielbereich; 0 entspricht der Untergrenze, 100 der Obergrenze."
        ),
    )
    target_position_change_points: int | None = Field(
        default=None,
        description=(
            "Differenz der relativen Herzfrequenz-Reaktion zwischen älteren und "
            "neueren vergleichbaren Workouts in Prozentpunkten."
        ),
    )
    load_adjusted_trend: str = Field(
        default="insufficient_data",
        description=(
            "Deskriptive Einordnung des HF-Trends unter Berücksichtigung der "
            "durchschnittlichen Bike-Leistung vergleichbarer Workouts."
        ),
    )
    median_power_w: int | None = Field(default=None, ge=0)
    median_cadence_rpm: float | None = Field(default=None, ge=0)
    power_change_percent: int | None = Field(
        default=None,
        description=(
            "Relative Änderung der mittleren Bike-Leistung zwischen älteren und "
            "neueren vergleichbaren Workouts."
        ),
    )


class LoadResponseResponse(BaseModel):
    """Deskriptiver Kontext aus HF, Bike-Belastung und heutiger Readiness."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    status: str
    workout_type: str
    comparable_workout_count: int = Field(ge=0)
    heart_rate_trend: str
    load_adjusted_heart_rate_trend: str
    median_power_w: int | None = Field(default=None, ge=0)
    median_cadence_rpm: float | None = Field(default=None, ge=0)
    readiness_caution: bool


class AdaptiveWorkoutDecisionContextResponse(BaseModel):
    """Deterministischer Eingabe-Snapshot einer adaptiven Entscheidung."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    workout_type: str
    available_training_minutes: int = Field(ge=1)
    readiness_max_duration_minutes: int | None = Field(default=None, ge=1)
    heart_rate_history_status: str
    heart_rate_history_max_duration_minutes: int | None = Field(default=None, ge=1)
    load_response_status: str
    comparable_workout_count: int = Field(ge=0)
    readiness_caution: bool


class AdaptiveWorkoutAdviceResponse(BaseModel):
    """Deterministischer, konservativer Anpassungsvorschlag fuer den heutigen Plan."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    action: str
    reason_codes: list[str] = Field(default_factory=list)
    plan_reflects_advice: bool = Field(
        description=(
            "Gibt an, ob der aktuelle Trainingsplan den Vorschlag bereits beruecksichtigt."
        )
    )
    recommended_duration_minutes: int | None = Field(default=None, ge=1)
    decision_context: AdaptiveWorkoutDecisionContextResponse


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
    load_response: LoadResponseResponse | None = Field(
        default=None,
        description=(
            "Rein deskriptiver Belastungsreaktions-Kontext. Er verändert keine "
            "Trainingsparameter automatisch."
        ),
    )
    adaptive_workout_advice: AdaptiveWorkoutAdviceResponse | None = Field(
        default=None,
        description=(
            "Deterministischer, konservativer Anpassungsvorschlag. Nicht bereits "
            "im Plan reflektierte Vorschlaege werden nicht automatisch angewendet."
        ),
    )
    heart_rate_history: HeartRateHistoryResponse | None = Field(
        default=None,
        description=(
            "Verdichtete Reaktion der Herzfrequenz in früheren auswertbaren Workouts. "
            "Eine hohe historische Reaktion kann die heutige Dauer konservativ begrenzen, "
            "erhöht aber niemals Zielpuls- oder Safety-Grenzen."
        ),
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
