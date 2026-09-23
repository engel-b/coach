from dataclasses import dataclass
from enum import StrEnum

from features.training.domain.heart_rate_history import HeartRateHistoryContext
from features.training.domain.heart_rate_target import HeartRateTargetSource
from features.training.domain.pre_workout import RecommendationReasonCode
from features.training.domain.weight_goal_progress import WeightGoalProgress


class WorkoutType(StrEnum):
    RECOVERY = "recovery"
    BASE_ENDURANCE = "base_endurance"
    MODERATE = "moderate"


class HeartRateTargetMethod(StrEnum):
    HEART_RATE_RESERVE = "heart_rate_reserve"
    MAX_HEART_RATE_PERCENTAGE = "max_heart_rate_percentage"


@dataclass(frozen=True)
class HeartRateTargetBasis:
    method: HeartRateTargetMethod
    max_heart_rate_bpm: int
    resting_heart_rate_bpm: int | None
    reference_resting_heart_rate_bpm: int | None
    resting_heart_rate_source: HeartRateTargetSource | None = None
    resting_heart_rate_sample_count: int = 0


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
    weight_goal_progress: WeightGoalProgress | None = None
    heart_rate_target_basis: HeartRateTargetBasis | None = None
    heart_rate_history: HeartRateHistoryContext | None = None
