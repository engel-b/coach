from dataclasses import dataclass
from enum import StrEnum

from features.training.domain.pre_workout import RecommendationReasonCode


class WorkoutType(StrEnum):
    RECOVERY = "recovery"
    BASE_ENDURANCE = "base_endurance"
    MODERATE = "moderate"


class WorkoutPhaseType(StrEnum):
    WARM_UP = "warm_up"
    MAIN = "main"
    COOL_DOWN = "cool_down"


@dataclass(frozen=True)
class WorkoutPhase:
    phase_type: WorkoutPhaseType
    duration_minutes: int
    target_heart_rate_min: int
    target_heart_rate_max: int


@dataclass(frozen=True)
class TrainingRecommendation:
    workout_type: WorkoutType
    total_duration_minutes: int
    reason: str
    phases: tuple[WorkoutPhase, ...]
    reason_codes: tuple[RecommendationReasonCode, ...] = ()
