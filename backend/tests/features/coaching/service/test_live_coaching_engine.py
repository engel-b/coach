import pytest

from features.coaching.domain.live_coaching import (
    CoachingAction,
    HeartRateZoneStatus,
    LiveCoachingContext,
    LiveCoachingRules,
)
from features.coaching.service.live_coaching_engine import (
    InvalidLiveCoachingContextError,
    LiveCoachingEngine,
)


def create_context(
    *,
    heart_rate_bpm: int,
    outside_target_seconds: float = 0.0,
    target_min_bpm: int = 125,
    target_max_bpm: int = 145,
) -> LiveCoachingContext:
    return LiveCoachingContext(
        heart_rate_bpm=heart_rate_bpm,
        target_min_bpm=target_min_bpm,
        target_max_bpm=target_max_bpm,
        outside_target_seconds=outside_target_seconds,
    )


def test_heart_rate_in_target_requires_no_action() -> None:
    engine = LiveCoachingEngine()

    decision = engine.evaluate(create_context(heart_rate_bpm=138))

    assert decision.zone_status == HeartRateZoneStatus.IN_TARGET
    assert decision.action == CoachingAction.NONE
    assert decision.reason == "heart_rate_in_target"


def test_target_boundaries_are_inside_target() -> None:
    engine = LiveCoachingEngine()

    minimum = engine.evaluate(create_context(heart_rate_bpm=125))
    maximum = engine.evaluate(create_context(heart_rate_bpm=145))

    assert minimum.zone_status == HeartRateZoneStatus.IN_TARGET
    assert minimum.action == CoachingAction.NONE
    assert maximum.zone_status == HeartRateZoneStatus.IN_TARGET
    assert maximum.action == CoachingAction.NONE


def test_short_deviation_below_target_requires_no_action() -> None:
    engine = LiveCoachingEngine()

    decision = engine.evaluate(
        create_context(
            heart_rate_bpm=118,
            outside_target_seconds=19.9,
        )
    )

    assert decision.zone_status == HeartRateZoneStatus.BELOW_TARGET
    assert decision.action == CoachingAction.NONE
    assert decision.reason == "deviation_too_short"


def test_long_enough_deviation_below_target_increases_intensity() -> None:
    engine = LiveCoachingEngine()

    decision = engine.evaluate(
        create_context(
            heart_rate_bpm=118,
            outside_target_seconds=20.0,
        )
    )

    assert decision.zone_status == HeartRateZoneStatus.BELOW_TARGET
    assert decision.action == CoachingAction.INCREASE_INTENSITY
    assert decision.reason == "heart_rate_below_target_long_enough"


def test_short_deviation_above_target_requires_no_action() -> None:
    engine = LiveCoachingEngine()

    decision = engine.evaluate(
        create_context(
            heart_rate_bpm=150,
            outside_target_seconds=5.0,
        )
    )

    assert decision.zone_status == HeartRateZoneStatus.ABOVE_TARGET
    assert decision.action == CoachingAction.NONE
    assert decision.reason == "deviation_too_short"


def test_long_enough_deviation_above_target_reduces_intensity() -> None:
    engine = LiveCoachingEngine()

    decision = engine.evaluate(
        create_context(
            heart_rate_bpm=150,
            outside_target_seconds=25.0,
        )
    )

    assert decision.zone_status == HeartRateZoneStatus.ABOVE_TARGET
    assert decision.action == CoachingAction.REDUCE_INTENSITY
    assert decision.reason == "heart_rate_above_target_long_enough"


def test_deviation_threshold_is_configurable() -> None:
    engine = LiveCoachingEngine(rules=LiveCoachingRules(deviation_seconds_before_action=30.0))

    before_threshold = engine.evaluate(
        create_context(heart_rate_bpm=150, outside_target_seconds=29.9)
    )
    at_threshold = engine.evaluate(create_context(heart_rate_bpm=150, outside_target_seconds=30.0))

    assert before_threshold.action == CoachingAction.NONE
    assert at_threshold.action == CoachingAction.REDUCE_INTENSITY


def test_invalid_target_range_is_rejected() -> None:
    engine = LiveCoachingEngine()

    with pytest.raises(InvalidLiveCoachingContextError):
        engine.evaluate(
            create_context(
                heart_rate_bpm=130,
                target_min_bpm=150,
                target_max_bpm=120,
            )
        )


def test_negative_outside_target_duration_is_rejected() -> None:
    engine = LiveCoachingEngine()

    with pytest.raises(InvalidLiveCoachingContextError):
        engine.evaluate(
            create_context(
                heart_rate_bpm=130,
                outside_target_seconds=-1.0,
            )
        )


def test_target_tolerance_avoids_coaching_for_small_deviation() -> None:
    engine = LiveCoachingEngine(
        rules=LiveCoachingRules(
            deviation_seconds_before_action=20.0,
            target_tolerance_bpm=5,
        )
    )

    decision = engine.evaluate(
        LiveCoachingContext(
            heart_rate_bpm=144,
            target_min_bpm=126,
            target_max_bpm=140,
            outside_target_seconds=60.0,
        )
    )

    assert decision.zone_status is HeartRateZoneStatus.IN_TARGET
    assert decision.action is CoachingAction.NONE
