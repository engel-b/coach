import asyncio
import logging
from datetime import UTC, datetime
from typing import Literal, Protocol

from features.coaching.api.contracts.live_coaching import (
    LiveCoachingEvent,
    LiveCoachingRuntimeEvent,
)
from features.coaching.domain.live_coaching import LiveCoachingDecision
from features.telemetry.domain.health.heart_rate import HeartRateSample

logger = logging.getLogger(__name__)

RuntimeCoachingEventType = Literal["coaching.pause_started", "coaching.pause_ended"]


class LiveCoachingBroadcastPort(Protocol):
    async def broadcast(self, message: str) -> None: ...


class LiveCoachingEventPublisher:
    """Brücke zwischen synchronem Coaching-Lifecycle und WebSocket-Ausgabe."""

    def __init__(self, *, broadcaster: LiveCoachingBroadcastPort) -> None:
        self._broadcaster = broadcaster

    def publish(
        self,
        workout_id: str,
        sample: HeartRateSample,
        decision: LiveCoachingDecision,
    ) -> None:
        event = LiveCoachingEvent.from_decision(
            workout_id=workout_id,
            sample=sample,
            decision=decision,
        )
        self._schedule(event.model_dump_json(by_alias=True))

    def publish_runtime_event(
        self,
        workout_id: str,
        event_type: RuntimeCoachingEventType,
    ) -> None:
        event = LiveCoachingRuntimeEvent(
            type=event_type,
            timestamp=datetime.now(UTC),
            workout_id=workout_id,
        )
        self._schedule(event.model_dump_json(by_alias=True))

    def _schedule(self, message: str) -> None:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            logger.warning("Live coaching event dropped because no event loop is running")
            return

        loop.create_task(self._broadcaster.broadcast(message))
