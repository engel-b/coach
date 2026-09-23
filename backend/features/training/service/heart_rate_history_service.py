from statistics import median

from features.training.domain.heart_rate_history import (
    HeartRateHistoryContext,
    HeartRateHistoryRules,
    HeartRateHistoryStatus,
)
from features.training.domain.recommendation import WorkoutType
from features.workout.domain.session import WorkoutSession, WorkoutStatus


class HeartRateHistoryService:
    """
    Verdichtet die Herzfrequenz-Reaktion aus abgeschlossenen Workouts.

    Die Historie darf Trainingsentscheidungen nur konservativ beeinflussen.
    Insbesondere wird aus einer hohen historischen Herzfrequenz niemals eine
    höhere Ziel-Herzfrequenz oder eine höhere Trainingsintensität abgeleitet.
    """

    def __init__(self, *, rules: HeartRateHistoryRules | None = None) -> None:
        self._rules = rules or HeartRateHistoryRules()

    def analyze(
        self,
        *,
        workouts: list[WorkoutSession],
        workout_type: WorkoutType,
    ) -> HeartRateHistoryContext:
        eligible = [
            workout
            for workout in workouts
            if workout.status is WorkoutStatus.COMPLETED
            and workout.workout_type is workout_type
            and workout.heart_rate_summary is not None
            and workout.heart_rate_summary.sample_count >= self._rules.min_samples_per_workout
        ][: self._rules.lookback_workouts]

        if len(eligible) < self._rules.min_workout_count:
            return HeartRateHistoryContext(
                status=HeartRateHistoryStatus.INSUFFICIENT_DATA,
                workout_count=len(eligible),
                workout_type=workout_type,
            )

        in_target = round(
            median(
                workout.heart_rate_summary.in_target_percent
                for workout in eligible
                if workout.heart_rate_summary is not None
            )
        )
        above = round(
            median(
                workout.heart_rate_summary.above_target_percent
                for workout in eligible
                if workout.heart_rate_summary is not None
            )
        )
        below = round(
            median(
                workout.heart_rate_summary.below_target_percent
                for workout in eligible
                if workout.heart_rate_summary is not None
            )
        )

        if above >= self._rules.dominant_outside_target_percent:
            status = HeartRateHistoryStatus.MOSTLY_ABOVE_TARGET
            duration_cap = self._rules.high_response_duration_cap_minutes
        elif below >= self._rules.dominant_outside_target_percent:
            status = HeartRateHistoryStatus.MOSTLY_BELOW_TARGET
            duration_cap = None
        elif in_target >= self._rules.mostly_in_target_percent:
            status = HeartRateHistoryStatus.MOSTLY_IN_TARGET
            duration_cap = None
        else:
            status = HeartRateHistoryStatus.MIXED
            duration_cap = None

        return HeartRateHistoryContext(
            status=status,
            workout_count=len(eligible),
            workout_type=workout_type,
            median_in_target_percent=in_target,
            median_above_target_percent=above,
            median_below_target_percent=below,
            max_duration_minutes=duration_cap,
        )
