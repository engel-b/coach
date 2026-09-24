from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING

from features.training.domain.heart_rate_history import (
    HeartRateResponseTrend,
    LoadAdjustedHeartRateTrend,
)
if TYPE_CHECKING:
    from features.training.domain.recommendation import WorkoutType


class LoadResponseStatus(StrEnum):
    """Deskriptive Einordnung der Reaktion auf vergleichbare Trainingsbelastung."""

    INSUFFICIENT_DATA = "insufficient_data"
    STABLE = "stable"
    LOWER_HR_AT_SIMILAR_LOAD = "lower_hr_at_similar_load"
    HIGHER_HR_AT_SIMILAR_LOAD = "higher_hr_at_similar_load"
    LOWER_LOAD = "lower_load"
    HIGHER_LOAD = "higher_load"
    MIXED = "mixed"


@dataclass(frozen=True)
class LoadResponseContext:
    """
    Zusammengeführter, rein deskriptiver Belastungsreaktions-Kontext.

    Der Kontext darf keine Trainingsparameter erhöhen. Er fasst bereits
    deterministisch abgeleitete Historien- und Readiness-Signale zusammen,
    damit UI und spätere adaptive Policies eine stabile fachliche Grundlage
    verwenden können.
    """

    status: LoadResponseStatus
    workout_type: WorkoutType
    comparable_workout_count: int
    heart_rate_trend: HeartRateResponseTrend
    load_adjusted_heart_rate_trend: LoadAdjustedHeartRateTrend
    median_power_w: int | None
    median_cadence_rpm: float | None
    readiness_caution: bool
