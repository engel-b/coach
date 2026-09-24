from dataclasses import dataclass, field
from enum import StrEnum

from features.check_in.domain.check_in import CheckIn
from features.person.domain.profile import TrainingGoal
from features.training.domain.heart_rate_history import (
    HeartRateHistoryContext,
    HeartRateHistoryStatus,
)
from features.training.domain.heart_rate_target import HeartRateTargetSource
from features.training.domain.load_response import LoadResponseContext
from features.training.domain.readiness import ReadinessContext
from features.training.domain.weight_goal_progress import WeightGoalProgress
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
    DURATION_REDUCED_FOR_HEART_RATE_HISTORY = "duration_reduced_for_heart_rate_history"
    READINESS_GOOD = "readiness_good"
    WEIGHT_LOSS_GOAL = "weight_loss_goal"
    WEIGHT_TREND_DOWN = "weight_trend_down"
    WEIGHT_TREND_STABLE = "weight_trend_stable"
    WEIGHT_TREND_UP = "weight_trend_up"
    WEIGHT_TREND_UNKNOWN = "weight_trend_unknown"
    WEIGHT_GOAL_NOT_CONFIGURED = "weight_goal_not_configured"
    WEIGHT_GOAL_NO_CURRENT_WEIGHT = "weight_goal_no_current_weight"
    WEIGHT_GOAL_ABOVE_TARGET = "weight_goal_above_target"
    WEIGHT_GOAL_AT_TARGET = "weight_goal_at_target"
    WEIGHT_GOAL_BELOW_TARGET = "weight_goal_below_target"
    HEART_RATE_HISTORY_IN_TARGET = "heart_rate_history_in_target"
    HEART_RATE_HISTORY_ABOVE_TARGET = "heart_rate_history_above_target"
    HEART_RATE_HISTORY_BELOW_TARGET = "heart_rate_history_below_target"
    HEART_RATE_HISTORY_MIXED = "heart_rate_history_mixed"


@dataclass(frozen=True)
class PreWorkoutCoachingContext:
    check_in: CheckIn
    max_heart_rate: int
    training_goal: TrainingGoal
    weight_trend: WeightTrend
    weight_goal_progress: WeightGoalProgress
    readiness: ReadinessContext
    heart_rate_history: HeartRateHistoryContext = field(
        default_factory=lambda: HeartRateHistoryContext(
            status=HeartRateHistoryStatus.INSUFFICIENT_DATA,
            workout_count=0,
        )
    )
    load_response: LoadResponseContext | None = None
    resting_heart_rate: int | None = None
    resting_heart_rate_source: HeartRateTargetSource | None = None
    resting_heart_rate_sample_count: int = 0
