from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from features.training.domain.recommendation import WorkoutType


class HeartRateResponseTrend(StrEnum):
    INSUFFICIENT_DATA = "insufficient_data"
    LOWER = "lower"
    STABLE = "stable"
    HIGHER = "higher"


class LoadAdjustedHeartRateTrend(StrEnum):
    INSUFFICIENT_DATA = "insufficient_data"
    LOWER_AT_SIMILAR_POWER = "lower_at_similar_power"
    HIGHER_AT_SIMILAR_POWER = "higher_at_similar_power"
    STABLE_AT_SIMILAR_POWER = "stable_at_similar_power"
    LOWER_WITH_LOWER_POWER = "lower_with_lower_power"
    HIGHER_WITH_HIGHER_POWER = "higher_with_higher_power"
    LOAD_CHANGED = "load_changed"


class HeartRateHistoryStatus(StrEnum):
    INSUFFICIENT_DATA = "insufficient_data"
    MOSTLY_IN_TARGET = "mostly_in_target"
    MOSTLY_ABOVE_TARGET = "mostly_above_target"
    MOSTLY_BELOW_TARGET = "mostly_below_target"
    MIXED = "mixed"


@dataclass(frozen=True)
class HeartRateHistoryRules:
    lookback_workouts: int = 6
    min_workout_count: int = 3
    min_samples_per_workout: int = 30
    mostly_in_target_percent: int = 60
    dominant_outside_target_percent: int = 40
    high_response_duration_cap_minutes: int = 30
    trend_min_workout_count: int = 4
    trend_change_threshold_points: int = 15
    min_power_samples_per_workout: int = 30
    min_cadence_samples_per_workout: int = 30
    similar_power_change_percent: int = 10


@dataclass(frozen=True)
class HeartRateHistoryContext:
    status: HeartRateHistoryStatus
    workout_count: int
    workout_type: WorkoutType | None = None
    median_in_target_percent: int | None = None
    median_above_target_percent: int | None = None
    median_below_target_percent: int | None = None
    max_duration_minutes: int | None = None
    response_trend: HeartRateResponseTrend = HeartRateResponseTrend.INSUFFICIENT_DATA
    median_target_position_percent: int | None = None
    target_position_change_points: int | None = None
    load_adjusted_trend: LoadAdjustedHeartRateTrend = LoadAdjustedHeartRateTrend.INSUFFICIENT_DATA
    median_power_w: int | None = None
    power_change_percent: int | None = None
    median_cadence_rpm: float | None = None
