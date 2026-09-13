import pytest

from features.coaching.domain.live_coaching import HeartRateZoneStatus
from features.coaching.service.heart_rate_deviation_tracker import (
    HeartRateDeviationTracker,
)


def test_heart_rate_in_target_has_no_deviation() -> None:
    tracker = HeartRateDeviationTracker()

    result = tracker.update(
        timestamp_seconds=10.0,
        heart_rate_bpm=135,
        target_min_bpm=125,
        target_max_bpm=145,
    )

    assert result.zone_status is HeartRateZoneStatus.IN_TARGET
    assert result.outside_target_seconds == 0.0


def test_above_target_starts_deviation_at_zero() -> None:
    tracker = HeartRateDeviationTracker()

    result = tracker.update(
        timestamp_seconds=10.0,
        heart_rate_bpm=150,
        target_min_bpm=125,
        target_max_bpm=145,
    )

    assert result.zone_status is HeartRateZoneStatus.ABOVE_TARGET
    assert result.outside_target_seconds == 0.0


def test_above_target_accumulates_deviation_time() -> None:
    tracker = HeartRateDeviationTracker()

    tracker.update(
        timestamp_seconds=10.0,
        heart_rate_bpm=150,
        target_min_bpm=125,
        target_max_bpm=145,
    )

    result = tracker.update(
        timestamp_seconds=31.0,
        heart_rate_bpm=148,
        target_min_bpm=125,
        target_max_bpm=145,
    )

    assert result.zone_status is HeartRateZoneStatus.ABOVE_TARGET
    assert result.outside_target_seconds == 21.0


def test_below_target_accumulates_deviation_time() -> None:
    tracker = HeartRateDeviationTracker()

    tracker.update(
        timestamp_seconds=5.0,
        heart_rate_bpm=120,
        target_min_bpm=125,
        target_max_bpm=145,
    )

    result = tracker.update(
        timestamp_seconds=27.0,
        heart_rate_bpm=119,
        target_min_bpm=125,
        target_max_bpm=145,
    )

    assert result.zone_status is HeartRateZoneStatus.BELOW_TARGET
    assert result.outside_target_seconds == 22.0


def test_returning_to_target_resets_deviation() -> None:
    tracker = HeartRateDeviationTracker()

    tracker.update(
        timestamp_seconds=0.0,
        heart_rate_bpm=150,
        target_min_bpm=125,
        target_max_bpm=145,
    )

    tracker.update(
        timestamp_seconds=25.0,
        heart_rate_bpm=150,
        target_min_bpm=125,
        target_max_bpm=145,
    )

    result = tracker.update(
        timestamp_seconds=30.0,
        heart_rate_bpm=140,
        target_min_bpm=125,
        target_max_bpm=145,
    )

    assert result.zone_status is HeartRateZoneStatus.IN_TARGET
    assert result.outside_target_seconds == 0.0


def test_switch_from_above_to_below_starts_new_deviation() -> None:
    tracker = HeartRateDeviationTracker()

    tracker.update(
        timestamp_seconds=0.0,
        heart_rate_bpm=150,
        target_min_bpm=125,
        target_max_bpm=145,
    )

    result = tracker.update(
        timestamp_seconds=25.0,
        heart_rate_bpm=120,
        target_min_bpm=125,
        target_max_bpm=145,
    )

    assert result.zone_status is HeartRateZoneStatus.BELOW_TARGET
    assert result.outside_target_seconds == 0.0


def test_exact_target_boundaries_are_in_target() -> None:
    tracker = HeartRateDeviationTracker()

    minimum = tracker.update(
        timestamp_seconds=0.0,
        heart_rate_bpm=125,
        target_min_bpm=125,
        target_max_bpm=145,
    )

    maximum = tracker.update(
        timestamp_seconds=1.0,
        heart_rate_bpm=145,
        target_min_bpm=125,
        target_max_bpm=145,
    )

    assert minimum.zone_status is HeartRateZoneStatus.IN_TARGET
    assert maximum.zone_status is HeartRateZoneStatus.IN_TARGET


@pytest.mark.parametrize(
    (
        "timestamp_seconds",
        "heart_rate_bpm",
        "target_min_bpm",
        "target_max_bpm",
    ),
    [
        (-1.0, 130, 125, 145),
        (0.0, 0, 125, 145),
        (0.0, 130, 0, 145),
        (0.0, 130, 125, 0),
        (0.0, 130, 150, 140),
    ],
)
def test_invalid_values_are_rejected(
    timestamp_seconds: float,
    heart_rate_bpm: int,
    target_min_bpm: int,
    target_max_bpm: int,
) -> None:
    tracker = HeartRateDeviationTracker()

    with pytest.raises(ValueError):
        tracker.update(
            timestamp_seconds=timestamp_seconds,
            heart_rate_bpm=heart_rate_bpm,
            target_min_bpm=target_min_bpm,
            target_max_bpm=target_max_bpm,
        )


def test_timestamp_must_not_move_backwards() -> None:
    tracker = HeartRateDeviationTracker()

    tracker.update(
        timestamp_seconds=10.0,
        heart_rate_bpm=150,
        target_min_bpm=125,
        target_max_bpm=145,
    )

    with pytest.raises(
        ValueError,
        match="timestamp_seconds must not move backwards",
    ):
        tracker.update(
            timestamp_seconds=9.0,
            heart_rate_bpm=150,
            target_min_bpm=125,
            target_max_bpm=145,
        )
