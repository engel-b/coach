from collections.abc import Callable

from features.coaching.domain.live_coaching import CoachingAction, LiveCoachingDecision
from features.coaching.service.live_coaching_coordinator import LiveCoachingCoordinator
from features.telemetry.domain.health.heart_rate import HeartRateSample
from features.workout.domain.session import WorkoutSession

LiveCoachingDecisionHandler = Callable[
    [str, HeartRateSample, LiveCoachingDecision],
    None,
]


class LiveCoachingLifecycle:
    """
    Verbindet Workout-Lifecycle und Herzfrequenz-Telemetrie mit dem Live Coach.

    Diese Orchestrierung liegt bewusst außerhalb der Feature-Pakete. Dadurch
    müssen weder workout noch telemetry das coaching-Feature kennen.

    V1-Annahme:
    Es wird genau ein Workout gleichzeitig live gecoacht. Startet ein neues
    Workout, übernimmt es den Coaching-Fokus.

    Nur konkrete Coaching-Aktionen werden an den optionalen Decision-Handler
    weitergegeben. Wiederholte identische Aktionen werden unterdrückt, bis sich
    die Herzfrequenz wieder normalisiert oder eine andere Aktion entsteht.
    """

    def __init__(
        self,
        *,
        coordinator: LiveCoachingCoordinator,
        decision_handler: LiveCoachingDecisionHandler | None = None,
    ) -> None:
        self._coordinator = coordinator
        self._decision_handler = decision_handler
        self._last_decision: LiveCoachingDecision | None = None
        self._last_emitted_action: CoachingAction | None = None

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
        self._last_emitted_action = None

    def handle_heart_rate(self, sample: HeartRateSample) -> None:
        decision = self._coordinator.handle_heart_rate(sample)
        self._last_decision = decision

        if decision is None or decision.action is CoachingAction.NONE:
            self._last_emitted_action = None
            return

        if decision.action is self._last_emitted_action:
            return

        workout_id = self._coordinator.active_workout_id
        if workout_id is None:
            return

        if self._decision_handler is not None:
            self._decision_handler(
                workout_id,
                sample,
                decision,
            )

        self._last_emitted_action = decision.action

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
        self._last_emitted_action = None
