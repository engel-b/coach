from features.coaching.domain.live_coaching import (
    CoachingAction,
    LiveCoachingRules,
)
from features.coaching.service.heart_rate_deviation_tracker import (
    HeartRateDeviationTracker,
)
from features.coaching.service.live_coaching_engine import LiveCoachingEngine
from features.coaching.service.live_coaching_service import LiveCoachingService


def create_service(
    deviation_seconds_before_action: float = 20.0,
) -> LiveCoachingService:
    return LiveCoachingService(
        deviation_tracker=HeartRateDeviationTracker(),
        coaching_engine=LiveCoachingEngine(
            rules=LiveCoachingRules(
                deviation_seconds_before_action=deviation_seconds_before_action,
            )
        ),
    )


def test_service_does_nothing_while_heart_rate_is_in_target() -> None:
    service = create_service()

    decision = service.evaluate_heart_rate(
        timestamp_seconds=0.0,
        heart_rate_bpm=135,
        target_min_bpm=125,
        target_max_bpm=145,
    )

    assert decision.action is CoachingAction.NONE


def test_service_does_not_react_to_short_high_heart_rate() -> None:
    service = create_service()

    service.evaluate_heart_rate(
        timestamp_seconds=0.0,
        heart_rate_bpm=150,
        target_min_bpm=125,
        target_max_bpm=145,
    )

    decision = service.evaluate_heart_rate(
        timestamp_seconds=10.0,
        heart_rate_bpm=151,
        target_min_bpm=125,
        target_max_bpm=145,
    )

    assert decision.action is CoachingAction.NONE


def test_service_reduces_intensity_after_sustained_high_heart_rate() -> None:
    service = create_service()

    service.evaluate_heart_rate(
        timestamp_seconds=0.0,
        heart_rate_bpm=150,
        target_min_bpm=125,
        target_max_bpm=145,
    )

    service.evaluate_heart_rate(
        timestamp_seconds=10.0,
        heart_rate_bpm=151,
        target_min_bpm=125,
        target_max_bpm=145,
    )

    decision = service.evaluate_heart_rate(
        timestamp_seconds=21.0,
        heart_rate_bpm=149,
        target_min_bpm=125,
        target_max_bpm=145,
    )

    assert decision.action is CoachingAction.REDUCE_INTENSITY


def test_service_increases_intensity_after_sustained_low_heart_rate() -> None:
    service = create_service()

    service.evaluate_heart_rate(
        timestamp_seconds=0.0,
        heart_rate_bpm=120,
        target_min_bpm=125,
        target_max_bpm=145,
    )

    decision = service.evaluate_heart_rate(
        timestamp_seconds=21.0,
        heart_rate_bpm=119,
        target_min_bpm=125,
        target_max_bpm=145,
    )

    assert decision.action is CoachingAction.INCREASE_INTENSITY


def test_return_to_target_resets_accumulated_deviation() -> None:
    service = create_service()

    service.evaluate_heart_rate(
        timestamp_seconds=0.0,
        heart_rate_bpm=150,
        target_min_bpm=125,
        target_max_bpm=145,
    )

    service.evaluate_heart_rate(
        timestamp_seconds=15.0,
        heart_rate_bpm=150,
        target_min_bpm=125,
        target_max_bpm=145,
    )

    service.evaluate_heart_rate(
        timestamp_seconds=16.0,
        heart_rate_bpm=140,
        target_min_bpm=125,
        target_max_bpm=145,
    )

    decision = service.evaluate_heart_rate(
        timestamp_seconds=25.0,
        heart_rate_bpm=150,
        target_min_bpm=125,
        target_max_bpm=145,
    )

    assert decision.action is CoachingAction.NONE
