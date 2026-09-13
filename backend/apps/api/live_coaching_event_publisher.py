import asyncio
import logging
from typing import Protocol

from features.coaching.api.contracts.live_coaching import LiveCoachingEvent
from features.coaching.domain.live_coaching import LiveCoachingDecision
from features.telemetry.domain.health.heart_rate import HeartRateSample

logger = logging.getLogger(__name__)


class LiveCoachingBroadcastPort(Protocol):
    async def broadcast(self, message: str) -> None: ...


class LiveCoachingEventPublisher:
    """
    Brücke zwischen synchronem Coaching-Lifecycle und asynchronem WebSocket.

    Herzfrequenz-Telemetrie wird innerhalb des FastAPI-Event-Loops verarbeitet.
    Der Publisher plant dort die asynchrone Verteilung des Events ein, ohne die
    fachliche Coaching-Logik von asyncio oder FastAPI abhängig zu machen.
    """

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

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            logger.warning("Live coaching event dropped because no event loop is running")
            return

        loop.create_task(
            self._broadcaster.broadcast(
                event.model_dump_json(by_alias=True),
            )
        )
