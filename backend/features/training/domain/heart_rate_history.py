from dataclasses import dataclass
from enum import StrEnum


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


@dataclass(frozen=True)
class HeartRateHistoryContext:
    status: HeartRateHistoryStatus
    workout_count: int
    median_in_target_percent: int | None = None
    median_above_target_percent: int | None = None
    median_below_target_percent: int | None = None
    max_duration_minutes: int | None = None
