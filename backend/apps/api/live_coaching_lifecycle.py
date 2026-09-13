from features.coaching.domain.live_coaching import LiveCoachingDecision
from features.coaching.service.live_coaching_coordinator import LiveCoachingCoordinator
from features.telemetry.domain.health.heart_rate import HeartRateSample
from features.workout.domain.session import WorkoutSession


class LiveCoachingLifecycle:
    """
    Verbindet den Workout-Lifecycle und die eingehende Herzfrequenz-Telemetrie
    mit dem LiveCoachingCoordinator.

    Diese Orchestrierung liegt bewusst außerhalb der Feature-Pakete. Dadurch
    müssen weder workout noch telemetry das coaching-Feature kennen.

    V1-Annahme:
    Es wird genau ein Workout gleichzeitig live gecoacht. Startet ein neues
    Workout, übernimmt es den Coaching-Fokus.
    """

    def __init__(
        self,
        *,
        coordinator: LiveCoachingCoordinator,
    ) -> None:
        self._coordinator = coordinator
        self._last_decision: LiveCoachingDecision | None = None

    @property
    def active_workout_id(self) -> str | None:
        return self._coordinator.active_workout_id

    @property
    def last_decision(self) -> LiveCoachingDecision | None:
        return self._last_decision

    def workout_started(self, workout: WorkoutSession) -> None:
        self._activate(workout)

    def workout_checkpointed(self, workout: WorkoutSession) -> None:
        self._activate(workout)

        self._coordinator.update_elapsed_seconds(
            workout_id=workout.id,
            elapsed_seconds=workout.elapsed_seconds,
        )

    def workout_finished(self, workout: WorkoutSession) -> None:
        if self._coordinator.active_workout_id != workout.id:
            return

        self._coordinator.finish(
            workout_id=workout.id,
        )
        self._last_decision = None

    def handle_heart_rate(self, sample: HeartRateSample) -> None:
        self._last_decision = self._coordinator.handle_heart_rate(sample)

    def _activate(self, workout: WorkoutSession) -> None:
        active_workout_id = self._coordinator.active_workout_id

        if active_workout_id == workout.id:
            return

        if active_workout_id is not None:
            self._coordinator.finish(
                workout_id=active_workout_id,
            )

        self._coordinator.start(workout)
        self._last_decision = None
