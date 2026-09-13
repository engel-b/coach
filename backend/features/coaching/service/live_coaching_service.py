from features.coaching.domain.live_coaching import (
    LiveCoachingContext,
    LiveCoachingDecision,
)
from features.coaching.service.heart_rate_deviation_tracker import (
    HeartRateDeviationTracker,
)
from features.coaching.service.live_coaching_engine import LiveCoachingEngine


class LiveCoachingService:
    """
    Orchestriert Pulsverlauf und Coaching-Entscheidung.

    Der Aufrufer liefert nur den aktuellen Herzfrequenzwert,
    den Zeitstempel und den Zielbereich.

    Wie lange der Puls bereits außerhalb des Zielbereichs liegt,
    wird intern durch den HeartRateDeviationTracker bestimmt.
    """

    def __init__(
        self,
        *,
        deviation_tracker: HeartRateDeviationTracker,
        coaching_engine: LiveCoachingEngine,
    ) -> None:
        self._deviation_tracker = deviation_tracker
        self._coaching_engine = coaching_engine

    def reset(self) -> None:
        """Setzt den zeitlichen Herzfrequenz-Kontext der Session zurück."""

        self._deviation_tracker.reset()

    def evaluate_heart_rate(
        self,
        *,
        timestamp_seconds: float,
        heart_rate_bpm: int,
        target_min_bpm: int,
        target_max_bpm: int,
    ) -> LiveCoachingDecision:
        deviation = self._deviation_tracker.update(
            timestamp_seconds=timestamp_seconds,
            heart_rate_bpm=heart_rate_bpm,
            target_min_bpm=target_min_bpm,
            target_max_bpm=target_max_bpm,
        )

        return self._coaching_engine.evaluate(
            LiveCoachingContext(
                heart_rate_bpm=heart_rate_bpm,
                target_min_bpm=target_min_bpm,
                target_max_bpm=target_max_bpm,
                outside_target_seconds=deviation.outside_target_seconds,
            )
        )
