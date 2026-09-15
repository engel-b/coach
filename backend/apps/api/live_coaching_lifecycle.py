from collections.abc import Callable
from typing import Literal

from features.coaching.domain.live_coaching import (
    CoachingAction,
    LiveCoachingDecision,
    LiveCoachingPhaseStarted,
)
from features.coaching.service.live_coaching_coordinator import LiveCoachingCoordinator
from features.telemetry.domain.health.heart_rate import HeartRateSample
from features.workout.domain.runtime import WorkoutRuntimeState
from features.workout.domain.session import WorkoutSession

LiveCoachingDecisionHandler = Callable[
    [str, HeartRateSample, LiveCoachingDecision],
    None,
]
RuntimeCoachingEventType = Literal["coaching.pause_started", "coaching.pause_ended"]
LiveCoachingRuntimeHandler = Callable[[str, RuntimeCoachingEventType], None]
LiveCoachingPhaseHandler = Callable[[str, LiveCoachingPhaseStarted], None]


class LiveCoachingLifecycle:
    """Orchestriert Workout-Lifecycle, Runtime-State und Live-Coaching."""

    def __init__(
        self,
        *,
        coordinator: LiveCoachingCoordinator,
        decision_handler: LiveCoachingDecisionHandler | None = None,
        runtime_handler: LiveCoachingRuntimeHandler | None = None,
        phase_handler: LiveCoachingPhaseHandler | None = None,
    ) -> None:
        self._coordinator = coordinator
        self._decision_handler = decision_handler
        self._runtime_handler = runtime_handler
        self._phase_handler = phase_handler
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

    def workout_checkpointed(
        self,
        workout: WorkoutSession,
        *,
        runtime_state: WorkoutRuntimeState = WorkoutRuntimeState.RUNNING,
    ) -> None:
        self._activate(workout)
        phase_started = self._coordinator.update_elapsed_seconds(
            workout_id=workout.id,
            elapsed_seconds=workout.elapsed_seconds,
        )
        if phase_started is not None and self._phase_handler is not None:
            self._phase_handler(workout.id, phase_started)
        self.workout_runtime_state_changed(
            workout_id=workout.id,
            runtime_state=runtime_state,
        )

    def workout_runtime_state_changed(
        self,
        *,
        workout_id: str,
        runtime_state: WorkoutRuntimeState,
    ) -> None:
        if self._coordinator.active_workout_id != workout_id:
            return

        previous_state = self._coordinator.runtime_state
        changed = self._coordinator.update_runtime_state(
            workout_id=workout_id,
            runtime_state=runtime_state,
        )
        if not changed:
            return

        self._last_decision = None
        self._last_emitted_action = None

        if self._runtime_handler is None:
            return

        if runtime_state is WorkoutRuntimeState.PAUSED:
            self._runtime_handler(workout_id, "coaching.pause_started")
        elif previous_state is WorkoutRuntimeState.PAUSED:
            self._runtime_handler(workout_id, "coaching.pause_ended")

    def workout_finished(self, workout: WorkoutSession) -> None:
        if self._coordinator.active_workout_id != workout.id:
            return

        self._coordinator.finish(workout_id=workout.id)
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
            self._decision_handler(workout_id, sample, decision)

        self._last_emitted_action = decision.action

    def _activate(self, workout: WorkoutSession) -> None:
        active_workout_id = self._coordinator.active_workout_id

        if active_workout_id == workout.id:
            return

        if active_workout_id is not None:
            self._coordinator.finish(workout_id=active_workout_id)

        self._coordinator.start(workout)
        self._last_decision = None
        self._last_emitted_action = None
