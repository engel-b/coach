from statistics import median

from features.training.domain.heart_rate_history import (
    HeartRateHistoryContext,
    HeartRateHistoryRules,
    HeartRateHistoryStatus,
    HeartRateResponseTrend,
)
from features.training.domain.recommendation import WorkoutPhaseType, WorkoutType
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

    @staticmethod
    def _target_position_percent(workout: WorkoutSession) -> float | None:
        summary = workout.heart_rate_summary
        if summary is None:
            return None

        main_phase = next(
            (phase for phase in workout.phases if phase.phase_type is WorkoutPhaseType.MAIN),
            None,
        )
        if main_phase is None:
            return None

        width = main_phase.target_heart_rate_max - main_phase.target_heart_rate_min
        if width <= 0:
            return None

        return (summary.average_bpm - main_phase.target_heart_rate_min) / width * 100.0

    def _response_trend(
        self,
        workouts: list[WorkoutSession],
    ) -> tuple[HeartRateResponseTrend, int | None, int | None]:
        # Repository history is newest-first. Reverse so the comparison is chronological.
        positions = [
            position
            for workout in reversed(workouts)
            if (position := self._target_position_percent(workout)) is not None
        ]
        if not positions:
            return HeartRateResponseTrend.INSUFFICIENT_DATA, None, None

        median_position = round(median(positions))
        if len(positions) < self._rules.trend_min_workout_count:
            return (
                HeartRateResponseTrend.INSUFFICIENT_DATA,
                median_position,
                None,
            )

        half = len(positions) // 2
        earlier = positions[:half]
        recent = positions[-half:]
        change = round(median(recent) - median(earlier))

        if change >= self._rules.trend_change_threshold_points:
            trend = HeartRateResponseTrend.HIGHER
        elif change <= -self._rules.trend_change_threshold_points:
            trend = HeartRateResponseTrend.LOWER
        else:
            trend = HeartRateResponseTrend.STABLE

        return trend, median_position, change

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

        response_trend, median_target_position, target_position_change = self._response_trend(
            eligible
        )

        if len(eligible) < self._rules.min_workout_count:
            return HeartRateHistoryContext(
                status=HeartRateHistoryStatus.INSUFFICIENT_DATA,
                workout_count=len(eligible),
                workout_type=workout_type,
                response_trend=response_trend,
                median_target_position_percent=median_target_position,
                target_position_change_points=target_position_change,
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
            response_trend=response_trend,
            median_target_position_percent=median_target_position,
            target_position_change_points=target_position_change,
        )
