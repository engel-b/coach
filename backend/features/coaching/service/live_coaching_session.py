from features.coaching.domain.live_coaching import (
    LiveCoachingDecision,
    LiveCoachingPhaseStarted,
)
from features.coaching.service.live_coaching_service import LiveCoachingService
from features.telemetry.domain.health.heart_rate import HeartRateSample
from features.workout.domain.phase_progress import get_current_phase
from features.workout.domain.runtime import WorkoutRuntimeState
from features.workout.domain.session import WorkoutSession, WorkoutStatus


class LiveCoachingSession:
    """
    Verbindet ein konkret laufendes Workout mit dem Live Coaching.

    Herzfrequenz-Coaching ist nur im Runtime-State ``running`` aktiv.
    Während Pause, Finish-Window und Overtime werden eingehende HR-Samples
    bewusst ignoriert. Bei jedem Runtime-State-Wechsel wird der zeitliche
    HR-Kontext zurückgesetzt, damit keine alte Abweichung weiterwirkt.
    """

    def __init__(
        self,
        *,
        workout: WorkoutSession,
        coaching_service: LiveCoachingService,
    ) -> None:
        if workout.status is not WorkoutStatus.RUNNING:
            raise ValueError("live coaching requires a running workout")

        self._workout = workout
        self._coaching_service = coaching_service
        self._elapsed_seconds = workout.elapsed_seconds
        self._runtime_state = WorkoutRuntimeState.RUNNING
        progress = get_current_phase(workout, elapsed_seconds=workout.elapsed_seconds)
        self._phase_index = progress.phase_index if progress is not None else None

    @property
    def workout_id(self) -> str:
        return self._workout.id

    @property
    def runtime_state(self) -> WorkoutRuntimeState:
        return self._runtime_state

    def update_elapsed_seconds(
        self,
        elapsed_seconds: int,
    ) -> LiveCoachingPhaseStarted | None:
        if elapsed_seconds < 0:
            raise ValueError("elapsed_seconds must not be negative")

        if elapsed_seconds < self._elapsed_seconds:
            raise ValueError("elapsed_seconds must not move backwards")

        self._elapsed_seconds = elapsed_seconds
        progress = get_current_phase(
            self._workout,
            elapsed_seconds=elapsed_seconds,
        )
        next_phase_index = progress.phase_index if progress is not None else None

        if next_phase_index == self._phase_index:
            return None

        self._coaching_service.reset()
        self._phase_index = next_phase_index

        if progress is None:
            return None

        phase = progress.phase
        return LiveCoachingPhaseStarted(
            phase_index=progress.phase_index,
            phase_type=phase.phase_type.value,
            duration_minutes=phase.duration_minutes,
            target_min_bpm=phase.target_heart_rate_min,
            target_max_bpm=phase.target_heart_rate_max,
        )

    def update_runtime_state(
        self,
        runtime_state: WorkoutRuntimeState,
    ) -> bool:
        """Setzt den Runtime-State und meldet, ob sich der State geändert hat."""

        if runtime_state is self._runtime_state:
            return False

        self._runtime_state = runtime_state
        self._coaching_service.reset()
        return True

    def handle_heart_rate(
        self,
        sample: HeartRateSample,
    ) -> LiveCoachingDecision | None:
        if self._runtime_state is not WorkoutRuntimeState.RUNNING:
            return None

        progress = get_current_phase(
            self._workout,
            elapsed_seconds=self._elapsed_seconds,
        )

        if progress is None:
            return None

        phase = progress.phase

        return self._coaching_service.evaluate_heart_rate(
            timestamp_seconds=sample.timestamp.timestamp(),
            heart_rate_bpm=sample.bpm,
            target_min_bpm=phase.target_heart_rate_min,
            target_max_bpm=phase.target_heart_rate_max,
        )
