from features.coaching.domain.live_coaching import LiveCoachingDecision
from features.coaching.service.heart_rate_deviation_tracker import (
    HeartRateDeviationTracker,
)
from features.coaching.service.live_coaching_engine import LiveCoachingEngine
from features.coaching.service.live_coaching_service import LiveCoachingService
from features.coaching.service.live_coaching_session import (
    LiveCoachingSession,
    LiveCoachingStructureEvent,
)
from features.telemetry.domain.health.heart_rate import HeartRateSample
from features.workout.domain.runtime import WorkoutRuntimeState
from features.workout.domain.session import WorkoutSession


class LiveCoachingCoordinator:
    """
    Verwaltet den Lifecycle des aktuell live gecoachten Workouts.

    V1-Annahme:
    Auf dem lokalen Coach gibt es genau ein gleichzeitig aktiv
    gecoachtes Workout.

    Der Coordinator verbindet dabei noch keine technische Ausgabe
    wie TTS oder WebSocket. Er liefert lediglich CoachingDecision.
    """

    def __init__(
        self,
        *,
        coaching_engine: LiveCoachingEngine,
    ) -> None:
        self._coaching_engine = coaching_engine
        self._session: LiveCoachingSession | None = None

    @property
    def active_workout_id(self) -> str | None:
        if self._session is None:
            return None

        return self._session.workout_id

    @property
    def runtime_state(self) -> WorkoutRuntimeState | None:
        if self._session is None:
            return None

        return self._session.runtime_state

    def start(
        self,
        workout: WorkoutSession,
    ) -> None:
        if self._session is not None:
            raise RuntimeError("a live coaching session is already active")

        self._session = LiveCoachingSession(
            workout=workout,
            coaching_service=LiveCoachingService(
                deviation_tracker=HeartRateDeviationTracker(),
                coaching_engine=self._coaching_engine,
            ),
        )

    def update_elapsed_seconds(
        self,
        *,
        workout_id: str,
        elapsed_seconds: int,
    ) -> tuple[LiveCoachingStructureEvent, ...]:
        session = self._require_session(workout_id)
        return session.update_elapsed_seconds(elapsed_seconds)

    def update_runtime_state(
        self,
        *,
        workout_id: str,
        runtime_state: WorkoutRuntimeState,
    ) -> bool:
        session = self._require_session(workout_id)
        return session.update_runtime_state(runtime_state)

    def handle_heart_rate(
        self,
        sample: HeartRateSample,
    ) -> LiveCoachingDecision | None:
        if self._session is None:
            return None

        return self._session.handle_heart_rate(sample)

    def finish(
        self,
        *,
        workout_id: str,
    ) -> None:
        self._require_session(workout_id)
        self._session = None

    def _require_session(
        self,
        workout_id: str,
    ) -> LiveCoachingSession:
        if self._session is None:
            raise RuntimeError("no live coaching session is active")

        if self._session.workout_id != workout_id:
            raise ValueError(f"workout {workout_id!r} is not the active coaching workout")

        return self._session
