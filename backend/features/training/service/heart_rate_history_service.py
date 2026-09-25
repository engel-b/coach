from statistics import median

from features.training.domain.heart_rate_history import (
    HeartRateHistoryContext,
    HeartRateHistoryRules,
    HeartRateHistoryStatus,
    HeartRateResponseTrend,
    LoadAdjustedHeartRateTrend,
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
            return HeartRateResponseTrend.INSUFFICIENT_DATA, median_position, None

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

    def _load_adjusted_trend(
        self,
        workouts: list[WorkoutSession],
        *,
        response_trend: HeartRateResponseTrend,
    ) -> tuple[LoadAdjustedHeartRateTrend, int | None, int | None]:
        # Nur Workouts mit ausreichend Power-Samples werden paarweise verglichen.
        pairs: list[tuple[float, int]] = []
        for workout in reversed(workouts):
            position = self._target_position_percent(workout)
            bike = workout.bike_summary
            if (
                position is None
                or bike is None
                or bike.average_power_w is None
                or bike.power_sample_count < self._rules.min_power_samples_per_workout
            ):
                continue
            pairs.append((position, bike.average_power_w))

        if not pairs:
            return LoadAdjustedHeartRateTrend.INSUFFICIENT_DATA, None, None

        median_power = round(median(power for _, power in pairs))
        if len(pairs) < self._rules.trend_min_workout_count:
            return LoadAdjustedHeartRateTrend.INSUFFICIENT_DATA, median_power, None

        half = len(pairs) // 2
        earlier = pairs[:half]
        recent = pairs[-half:]
        earlier_power = median(power for _, power in earlier)
        recent_power = median(power for _, power in recent)
        if earlier_power <= 0:
            return LoadAdjustedHeartRateTrend.INSUFFICIENT_DATA, median_power, None

        power_change = round((recent_power - earlier_power) / earlier_power * 100)
        similar_power = abs(power_change) <= self._rules.similar_power_change_percent

        if similar_power:
            if response_trend is HeartRateResponseTrend.LOWER:
                adjusted = LoadAdjustedHeartRateTrend.LOWER_AT_SIMILAR_POWER
            elif response_trend is HeartRateResponseTrend.HIGHER:
                adjusted = LoadAdjustedHeartRateTrend.HIGHER_AT_SIMILAR_POWER
            elif response_trend is HeartRateResponseTrend.STABLE:
                adjusted = LoadAdjustedHeartRateTrend.STABLE_AT_SIMILAR_POWER
            else:
                adjusted = LoadAdjustedHeartRateTrend.INSUFFICIENT_DATA
        elif response_trend is HeartRateResponseTrend.LOWER and power_change < 0:
            adjusted = LoadAdjustedHeartRateTrend.LOWER_WITH_LOWER_POWER
        elif response_trend is HeartRateResponseTrend.HIGHER and power_change > 0:
            adjusted = LoadAdjustedHeartRateTrend.HIGHER_WITH_HIGHER_POWER
        else:
            adjusted = LoadAdjustedHeartRateTrend.LOAD_CHANGED

        return adjusted, median_power, power_change

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
        load_adjusted_trend, median_power, power_change = self._load_adjusted_trend(
            eligible,
            response_trend=response_trend,
        )
        cadence_values = [
            workout.bike_summary.average_cadence_rpm
            for workout in eligible
            if workout.bike_summary is not None
            and workout.bike_summary.average_cadence_rpm is not None
            and workout.bike_summary.cadence_sample_count
            >= self._rules.min_cadence_samples_per_workout
        ]
        median_cadence = round(median(cadence_values), 1) if cadence_values else None

        if len(eligible) < self._rules.min_workout_count:
            return HeartRateHistoryContext(
                status=HeartRateHistoryStatus.INSUFFICIENT_DATA,
                workout_count=len(eligible),
                workout_type=workout_type,
                response_trend=response_trend,
                median_target_position_percent=median_target_position,
                target_position_change_points=target_position_change,
                load_adjusted_trend=load_adjusted_trend,
                median_power_w=median_power,
                power_change_percent=power_change,
                median_cadence_rpm=median_cadence,
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
            load_adjusted_trend=load_adjusted_trend,
            median_power_w=median_power,
            power_change_percent=power_change,
            median_cadence_rpm=median_cadence,
        )
