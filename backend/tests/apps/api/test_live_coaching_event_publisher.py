import asyncio
import json
from datetime import UTC, datetime

from apps.api.live_coaching_event_publisher import LiveCoachingEventPublisher
from features.coaching.domain.live_coaching import (
    CoachingAction,
    HeartRateDeviationSeverity,
    HeartRateZoneStatus,
    LiveCoachingDecision,
)
from features.telemetry.domain.health.heart_rate import HeartRateSample


class RecordingBroadcaster:
    def __init__(self) -> None:
        self.messages: list[str] = []

    async def broadcast(self, message: str) -> None:
        self.messages.append(message)


async def test_publisher_schedules_websocket_event() -> None:
    broadcaster = RecordingBroadcaster()
    publisher = LiveCoachingEventPublisher(
        broadcaster=broadcaster,
    )

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

    publisher.publish(
        "workout-1",
        sample,
        decision,
    )

    await asyncio.sleep(0)

    assert len(broadcaster.messages) == 1
    assert json.loads(broadcaster.messages[0]) == {
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


async def test_publisher_schedules_pause_runtime_event() -> None:
    broadcaster = RecordingBroadcaster()
    publisher = LiveCoachingEventPublisher(broadcaster=broadcaster)

    publisher.publish_runtime_event(
        "workout-1",
        "coaching.pause_started",
    )

    await asyncio.sleep(0)

    assert len(broadcaster.messages) == 1
    message = json.loads(broadcaster.messages[0])
    assert message["type"] == "coaching.pause_started"
    assert message["workoutId"] == "workout-1"
    assert isinstance(message["timestamp"], str)


async def test_publisher_schedules_phase_started_event() -> None:
    from features.coaching.domain.live_coaching import LiveCoachingPhaseStarted

    broadcaster = RecordingBroadcaster()
    publisher = LiveCoachingEventPublisher(broadcaster=broadcaster)

    publisher.publish_structure_event(
        "workout-1",
        LiveCoachingPhaseStarted(
            phase_index=1,
            phase_type="main",
            duration_minutes=20,
            target_min_bpm=125,
            target_max_bpm=145,
        ),
    )

    await asyncio.sleep(0)

    assert len(broadcaster.messages) == 1
    message = json.loads(broadcaster.messages[0])
    assert message["type"] == "coaching.phase_started"
    assert message["workoutId"] == "workout-1"
    assert message["phaseIndex"] == 1
    assert message["phaseType"] == "main"
    assert message["durationMinutes"] == 20
    assert message["targetMinBpm"] == 125
    assert message["targetMaxBpm"] == 145
    assert isinstance(message["timestamp"], str)
