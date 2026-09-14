from datetime import datetime, timedelta

from features.check_in.domain.check_in import CheckIn
from features.training.domain.weight_trend import (
    WeightTrend,
    WeightTrendDirection,
)


class WeightTrendService:
    """
    Ermittelt einen robusteren Gewichtstrend als ein einfacher
    Vergleich zweier Einzelmessungen.

    Verwendet wird eine lineare Regression über die verfügbaren
    Gewichtsmessungen innerhalb eines Zeitfensters. Weniger als drei
    Messungen oder weniger als sieben Tage Spannweite gelten noch nicht
    als belastbarer Trend.
    """

    def __init__(
        self,
        *,
        window_days: int = 30,
        stable_threshold_kg_per_week: float = 0.10,
    ) -> None:
        if window_days < 7:
            raise ValueError("window_days must be at least 7")
        if stable_threshold_kg_per_week < 0:
            raise ValueError("stable_threshold_kg_per_week must not be negative")

        self._window_days = window_days
        self._stable_threshold_kg_per_week = stable_threshold_kg_per_week

    def calculate(
        self,
        *,
        check_ins: list[CheckIn],
        as_of: datetime,
    ) -> WeightTrend:
        window_start = as_of - timedelta(days=self._window_days)

        samples = sorted(
            (
                check_in
                for check_in in check_ins
                if check_in.current_weight_kg is not None
                and window_start <= check_in.timestamp <= as_of
            ),
            key=lambda check_in: check_in.timestamp,
        )

        if len(samples) < 3:
            return self._unknown(sample_count=len(samples))

        first_timestamp = samples[0].timestamp
        span_days = (samples[-1].timestamp - first_timestamp).total_seconds() / 86400.0

        if span_days < 7.0:
            return self._unknown(
                sample_count=len(samples),
                span_days=span_days,
            )

        x_values = [
            (sample.timestamp - first_timestamp).total_seconds() / 86400.0 for sample in samples
        ]
        y_values = [
            sample.current_weight_kg for sample in samples if sample.current_weight_kg is not None
        ]

        x_mean = sum(x_values) / len(x_values)
        y_mean = sum(y_values) / len(y_values)

        denominator = sum((x - x_mean) ** 2 for x in x_values)
        if denominator == 0:
            return self._unknown(
                sample_count=len(samples),
                span_days=span_days,
            )

        slope_kg_per_day = (
            sum((x - x_mean) * (y - y_mean) for x, y in zip(x_values, y_values, strict=True))
            / denominator
        )
        weekly_change_kg = slope_kg_per_day * 7.0

        if abs(weekly_change_kg) < self._stable_threshold_kg_per_week:
            direction = WeightTrendDirection.STABLE
        elif weekly_change_kg < 0:
            direction = WeightTrendDirection.DOWN
        else:
            direction = WeightTrendDirection.UP

        return WeightTrend(
            direction=direction,
            weekly_change_kg=round(weekly_change_kg, 2),
            sample_count=len(samples),
            span_days=round(span_days, 1),
        )

    @staticmethod
    def _unknown(
        *,
        sample_count: int,
        span_days: float = 0.0,
    ) -> WeightTrend:
        return WeightTrend(
            direction=WeightTrendDirection.UNKNOWN,
            weekly_change_kg=None,
            sample_count=sample_count,
            span_days=round(span_days, 1),
        )
