from dataclasses import dataclass
from enum import StrEnum

from features.check_in.domain.check_in import CheckIn
from features.person.domain.profile import TrainingGoal
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


@dataclass(frozen=True)
class PreWorkoutCoachingContext:
    check_in: CheckIn
    max_heart_rate: int
    training_goal: TrainingGoal
    weight_trend: WeightTrend
    weight_goal_progress: WeightGoalProgress
    readiness: ReadinessContext
    resting_heart_rate: int | None = None
