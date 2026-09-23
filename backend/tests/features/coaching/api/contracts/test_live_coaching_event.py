from datetime import UTC, datetime

from features.coaching.api.contracts.live_coaching import LiveCoachingEvent
from features.coaching.domain.live_coaching import (
    CoachingAction,
    HeartRateDeviationSeverity,
    HeartRateZoneStatus,
    LiveCoachingDecision,
)
from features.telemetry.domain.health.heart_rate import HeartRateSample


def test_live_coaching_event_uses_camel_case_json_contract() -> None:
    sample = HeartRateSample(
        device_id="heart-rate-1",
        timestamp=datetime(2026, 9, 13, 8, 30, tzinfo=UTC),
        bpm=149,
    )
    decision = LiveCoachingDecision(
        action=CoachingAction.REDUCE_INTENSITY,
        zone_status=HeartRateZoneStatus.ABOVE_TARGET,
        heart_rate_bpm=149,
        target_min_bpm=125,
        target_max_bpm=145,
        outside_target_seconds=21.0,
        deviation_bpm=4,
        deviation_severity=HeartRateDeviationSeverity.MODERATE,
        reason="heart_rate_above_target_long_enough",
    )

    event = LiveCoachingEvent.from_decision(
        workout_id="workout-1",
        sample=sample,
        decision=decision,
    )

    assert event.model_dump(mode="json", by_alias=True) == {
        "type": "coaching.decision",
        "timestamp": "2026-09-13T08:30:00Z",
        "workoutId": "workout-1",
        "deviceId": "heart-rate-1",
        "action": "reduce_intensity",
        "zoneStatus": "above_target",
        "heartRateBpm": 149,
        "targetMinBpm": 125,
        "targetMaxBpm": 145,
        "outsideTargetSeconds": 21.0,
        "deviationBpm": 4,
        "deviationSeverity": "moderate",
        "reason": "heart_rate_above_target_long_enough",
    }


def test_live_coaching_runtime_event_uses_camel_case_json_contract() -> None:
    from features.coaching.api.contracts.live_coaching import LiveCoachingRuntimeEvent

    event = LiveCoachingRuntimeEvent(
        type="coaching.pause_started",
        timestamp=datetime(2026, 9, 13, 8, 30, tzinfo=UTC),
        workout_id="workout-1",
    )

    assert event.model_dump(mode="json", by_alias=True) == {
        "type": "coaching.pause_started",
        "timestamp": "2026-09-13T08:30:00Z",
        "workoutId": "workout-1",
    }


def test_phase_started_event_uses_camel_case_json_contract() -> None:
    from features.coaching.api.contracts.live_coaching import (
        LiveCoachingPhaseStartedEvent,
    )
    from features.coaching.domain.live_coaching import LiveCoachingPhaseStarted

    event = LiveCoachingPhaseStartedEvent.from_phase_started(
        workout_id="workout-1",
        timestamp=datetime(2026, 9, 13, 8, 35, tzinfo=UTC),
        phase_started=LiveCoachingPhaseStarted(
            phase_index=1,
            phase_type="main",
            duration_minutes=20,
            target_min_bpm=125,
            target_max_bpm=145,
        ),
    )

    assert event.model_dump(mode="json", by_alias=True) == {
        "type": "coaching.phase_started",
        "timestamp": "2026-09-13T08:35:00Z",
        "workoutId": "workout-1",
        "phaseIndex": 1,
        "phaseType": "main",
        "durationMinutes": 20,
        "targetMinBpm": 125,
        "targetMaxBpm": 145,
        "isFinalPhase": False,
    }
