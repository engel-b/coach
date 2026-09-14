from dataclasses import dataclass
from enum import StrEnum


class WeightTrendDirection(StrEnum):
    UNKNOWN = "unknown"
    DOWN = "down"
    STABLE = "stable"
    UP = "up"


@dataclass(frozen=True)
class WeightTrend:
    """Geglätteter Gewichtstrend aus mehreren Check-in-Messungen."""

    direction: WeightTrendDirection
    weekly_change_kg: float | None
    sample_count: int
    span_days: float
