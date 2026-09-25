from features.training.domain.heart_rate_history import (
    HeartRateHistoryContext,
    LoadAdjustedHeartRateTrend,
)
from features.training.domain.load_response import LoadResponseContext, LoadResponseStatus
from features.training.domain.readiness import ReadinessContext
from features.training.domain.recommendation import WorkoutType


class LoadResponseService:
    """Fasst historische HF-/Bike-Reaktion und heutige Readiness deskriptiv zusammen."""

    def assess(
        self,
        *,
        history: HeartRateHistoryContext,
        readiness: ReadinessContext,
        workout_type: WorkoutType,
    ) -> LoadResponseContext:
        adjusted = history.load_adjusted_trend

        status = {
            LoadAdjustedHeartRateTrend.LOWER_AT_SIMILAR_POWER: (
                LoadResponseStatus.LOWER_HR_AT_SIMILAR_LOAD
            ),
            LoadAdjustedHeartRateTrend.HIGHER_AT_SIMILAR_POWER: (
                LoadResponseStatus.HIGHER_HR_AT_SIMILAR_LOAD
            ),
            LoadAdjustedHeartRateTrend.STABLE_AT_SIMILAR_POWER: LoadResponseStatus.STABLE,
            LoadAdjustedHeartRateTrend.LOWER_WITH_LOWER_POWER: LoadResponseStatus.LOWER_LOAD,
            LoadAdjustedHeartRateTrend.HIGHER_WITH_HIGHER_POWER: LoadResponseStatus.HIGHER_LOAD,
            LoadAdjustedHeartRateTrend.LOAD_CHANGED: LoadResponseStatus.MIXED,
            LoadAdjustedHeartRateTrend.INSUFFICIENT_DATA: LoadResponseStatus.INSUFFICIENT_DATA,
        }[adjusted]

        return LoadResponseContext(
            status=status,
            workout_type=workout_type,
            comparable_workout_count=history.workout_count,
            heart_rate_trend=history.response_trend,
            load_adjusted_heart_rate_trend=adjusted,
            median_power_w=history.median_power_w,
            median_cadence_rpm=history.median_cadence_rpm,
            readiness_caution=readiness.max_duration_minutes is not None,
        )
