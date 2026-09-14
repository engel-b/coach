from datetime import UTC, datetime, timedelta

from features.check_in.domain.check_in import CheckIn
from features.training.domain.weight_trend import WeightTrendDirection
from features.training.service.weight_trend_service import WeightTrendService

NOW = datetime(2026, 9, 14, 8, 0, tzinfo=UTC)


def check_in(days_ago: int, weight: float | None) -> CheckIn:
    return CheckIn(
        person_id=1,
        timestamp=NOW - timedelta(days=days_ago),
        energy=3,
        recovery=3,
        muscle_soreness=1,
        stress=2,
        available_training_minutes=30,
        current_weight_kg=weight,
    )


def test_requires_at_least_three_weight_samples() -> None:
    trend = WeightTrendService().calculate(
        check_ins=[check_in(14, 90.0), check_in(0, 89.0)],
        as_of=NOW,
    )

    assert trend.direction is WeightTrendDirection.UNKNOWN
    assert trend.weekly_change_kg is None


def test_requires_at_least_seven_days_span() -> None:
    trend = WeightTrendService().calculate(
        check_ins=[
            check_in(5, 90.0),
            check_in(3, 89.8),
            check_in(0, 89.6),
        ],
        as_of=NOW,
    )

    assert trend.direction is WeightTrendDirection.UNKNOWN


def test_detects_downward_weight_trend() -> None:
    trend = WeightTrendService().calculate(
        check_ins=[
            check_in(21, 90.0),
            check_in(14, 89.5),
            check_in(7, 89.0),
            check_in(0, 88.5),
        ],
        as_of=NOW,
    )

    assert trend.direction is WeightTrendDirection.DOWN
    assert trend.weekly_change_kg == -0.5
    assert trend.sample_count == 4


def test_small_changes_are_classified_as_stable() -> None:
    trend = WeightTrendService().calculate(
        check_ins=[
            check_in(21, 90.00),
            check_in(14, 90.02),
            check_in(7, 89.98),
            check_in(0, 90.01),
        ],
        as_of=NOW,
    )

    assert trend.direction is WeightTrendDirection.STABLE


def test_ignores_missing_weights_and_samples_outside_window() -> None:
    trend = WeightTrendService(window_days=30).calculate(
        check_ins=[
            check_in(60, 100.0),
            check_in(21, 90.0),
            check_in(14, None),
            check_in(7, 90.5),
            check_in(0, 91.0),
        ],
        as_of=NOW,
    )

    assert trend.direction is WeightTrendDirection.UP
    assert trend.sample_count == 3
