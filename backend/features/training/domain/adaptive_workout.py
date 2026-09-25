from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING

from features.training.domain.heart_rate_history import HeartRateHistoryStatus
from features.training.domain.load_response import LoadResponseStatus

if TYPE_CHECKING:
    from features.training.domain.recommendation import WorkoutType


class AdaptiveWorkoutAction(StrEnum):
    """Konservative, deterministische Anpassungsoptionen vor einem Workout."""

    KEEP_PLAN = "keep_plan"
    REDUCE_DURATION = "reduce_duration"
    REDUCE_INTENSITY = "reduce_intensity"
    EXTEND_WARMUP = "extend_warmup"
    PREFER_RECOVERY = "prefer_recovery"


class AdaptiveWorkoutReasonCode(StrEnum):
    """Stabile Gründe für eine adaptive Empfehlung."""

    RECOVERY_PLAN_SELECTED = "recovery_plan_selected"
    READINESS_DURATION_CAP = "readiness_duration_cap"
    HEART_RATE_HISTORY_DURATION_CAP = "heart_rate_history_duration_cap"
    HIGHER_HR_AT_SIMILAR_LOAD = "higher_hr_at_similar_load"
    LOWER_HR_AT_SIMILAR_LOAD = "lower_hr_at_similar_load"
    NO_AUTOMATIC_PROGRESSION = "no_automatic_progression"
    INSUFFICIENT_COMPARABLE_DATA = "insufficient_comparable_data"


@dataclass(frozen=True)
class AdaptiveWorkoutDecisionContext:
    """Nachvollziehbarer Snapshot der Eingaben einer adaptiven Entscheidung."""

    workout_type: WorkoutType
    available_training_minutes: int
    readiness_max_duration_minutes: int | None
    heart_rate_history_status: HeartRateHistoryStatus
    heart_rate_history_max_duration_minutes: int | None
    load_response_status: LoadResponseStatus
    comparable_workout_count: int
    readiness_caution: bool


@dataclass(frozen=True)
class AdaptiveWorkoutAdvice:
    """
    Deterministischer Anpassungsvorschlag für die geplante Einheit.

    `plan_reflects_advice` bedeutet, dass der aktuelle Plan den Rat bereits
    berücksichtigt. Die Policy steuert kein Gerät und erhöht niemals die
    Trainingsintensität.

    `decision_context` hält die deterministisch bewerteten Eingangssignale fest,
    damit API, UI, Tests und Logs dieselbe Erklärung verwenden können.
    """

    action: AdaptiveWorkoutAction
    reason_codes: tuple[AdaptiveWorkoutReasonCode, ...]
    plan_reflects_advice: bool
    decision_context: AdaptiveWorkoutDecisionContext
    recommended_duration_minutes: int | None = None
