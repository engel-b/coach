from dataclasses import dataclass
from enum import StrEnum

from features.check_in.domain.check_in import CheckIn
from features.person.domain.profile import TrainingGoal
from features.training.domain.readiness import ReadinessContext
from features.training.domain.weight_trend import WeightTrend


class RecommendationReasonCode(StrEnum):
    LOW_ENERGY = "low_energy"
    LOW_RECOVERY = "low_recovery"
    HIGH_MUSCLE_SORENESS = "high_muscle_soreness"
    HIGH_STRESS = "high_stress"
    SHORT_SLEEP = "short_sleep"
    HIGH_DAILY_ACTIVITY = "high_daily_activity"
    HIGH_RECENT_TRAINING_LOAD = "high_recent_training_load"
    DURATION_REDUCED_FOR_READINESS = "duration_reduced_for_readiness"
    READINESS_GOOD = "readiness_good"
    WEIGHT_LOSS_GOAL = "weight_loss_goal"
    WEIGHT_TREND_DOWN = "weight_trend_down"
    WEIGHT_TREND_STABLE = "weight_trend_stable"
    WEIGHT_TREND_UP = "weight_trend_up"
    WEIGHT_TREND_UNKNOWN = "weight_trend_unknown"


@dataclass(frozen=True)
class PreWorkoutCoachingContext:
    check_in: CheckIn
    max_heart_rate: int
    training_goal: TrainingGoal
    weight_trend: WeightTrend
    readiness: ReadinessContext
