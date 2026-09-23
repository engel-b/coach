from features.coaching.domain.live_coaching import (
    LiveCoachingDecision,
    LiveCoachingPhaseEnding,
    LiveCoachingPhaseStarted,
    LiveCoachingStructureEvent,
    LiveCoachingWorkoutHalfway,
)
from features.coaching.service.live_coaching_service import LiveCoachingService
from features.telemetry.domain.health.heart_rate import HeartRateSample
from features.workout.domain.heart_rate_summary import WorkoutHeartRateSummary
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
        self._main_hr_sample_count = 0
        self._main_hr_sum_bpm = 0
        self._main_hr_max_bpm: int | None = None
        self._main_hr_below_target_count = 0
        self._main_hr_in_target_count = 0
        self._main_hr_above_target_count = 0

    @property
    def workout_id(self) -> str:
        return self._workout.id

    @property
    def runtime_state(self) -> WorkoutRuntimeState:
        return self._runtime_state

    def update_elapsed_seconds(
        self,
        elapsed_seconds: int,
    ) -> tuple[LiveCoachingStructureEvent, ...]:
        if elapsed_seconds < 0:
            raise ValueError("elapsed_seconds must not be negative")

        if elapsed_seconds < self._elapsed_seconds:
            raise ValueError("elapsed_seconds must not move backwards")

        previous_elapsed_seconds = self._elapsed_seconds
        self._elapsed_seconds = elapsed_seconds
        events = self._structure_events_crossed(
            previous_elapsed_seconds=previous_elapsed_seconds,
            elapsed_seconds=elapsed_seconds,
        )

        progress = get_current_phase(
            self._workout,
            elapsed_seconds=elapsed_seconds,
        )
        next_phase_index = progress.phase_index if progress is not None else None

        if next_phase_index != self._phase_index:
            self._coaching_service.reset()
            self._phase_index = next_phase_index

        return events

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

        if phase.phase_type.value == "main":
            self._record_main_heart_rate(
                heart_rate_bpm=sample.bpm,
                target_min_bpm=phase.target_heart_rate_min,
                target_max_bpm=phase.target_heart_rate_max,
            )

        return self._coaching_service.evaluate_heart_rate(
            timestamp_seconds=sample.timestamp.timestamp(),
            heart_rate_bpm=sample.bpm,
            target_min_bpm=phase.target_heart_rate_min,
            target_max_bpm=phase.target_heart_rate_max,
        )

    def heart_rate_summary(self) -> WorkoutHeartRateSummary | None:
        if self._main_hr_sample_count == 0 or self._main_hr_max_bpm is None:
            return None

        def percent(count: int) -> int:
            return round(count / self._main_hr_sample_count * 100)

        return WorkoutHeartRateSummary(
            sample_count=self._main_hr_sample_count,
            average_bpm=round(self._main_hr_sum_bpm / self._main_hr_sample_count),
            max_bpm=self._main_hr_max_bpm,
            below_target_percent=percent(self._main_hr_below_target_count),
            in_target_percent=percent(self._main_hr_in_target_count),
            above_target_percent=percent(self._main_hr_above_target_count),
        )

    def _record_main_heart_rate(
        self,
        *,
        heart_rate_bpm: int,
        target_min_bpm: int,
        target_max_bpm: int,
    ) -> None:
        self._main_hr_sample_count += 1
        self._main_hr_sum_bpm += heart_rate_bpm
        self._main_hr_max_bpm = (
            heart_rate_bpm
            if self._main_hr_max_bpm is None
            else max(self._main_hr_max_bpm, heart_rate_bpm)
        )

        if heart_rate_bpm < target_min_bpm:
            self._main_hr_below_target_count += 1
        elif heart_rate_bpm > target_max_bpm:
            self._main_hr_above_target_count += 1
        else:
            self._main_hr_in_target_count += 1

    def _structure_events_crossed(
        self,
        *,
        previous_elapsed_seconds: int,
        elapsed_seconds: int,
    ) -> tuple[LiveCoachingStructureEvent, ...]:
        if elapsed_seconds == previous_elapsed_seconds:
            return ()

        scheduled: list[tuple[int, LiveCoachingStructureEvent]] = []
        phase_start_seconds = 0
        phase_count = len(self._workout.phases)

        for phase_index, phase in enumerate(self._workout.phases):
            phase_duration_seconds = phase.duration_minutes * 60
            phase_end_seconds = phase_start_seconds + phase_duration_seconds

            if phase_index > 0:
                scheduled.append(
                    (
                        phase_start_seconds,
                        LiveCoachingPhaseStarted(
                            phase_index=phase_index,
                            phase_type=phase.phase_type.value,
                            duration_minutes=phase.duration_minutes,
                            target_min_bpm=phase.target_heart_rate_min,
                            target_max_bpm=phase.target_heart_rate_max,
                            is_final_phase=phase_index == phase_count - 1,
                        ),
                    )
                )

            one_minute_before_end = phase_end_seconds - 60
            if phase_duration_seconds > 60:
                scheduled.append(
                    (
                        one_minute_before_end,
                        LiveCoachingPhaseEnding(
                            phase_index=phase_index,
                            phase_type=phase.phase_type.value,
                            remaining_seconds=60,
                        ),
                    )
                )

            phase_start_seconds = phase_end_seconds

        total_duration_seconds = sum(phase.duration_minutes * 60 for phase in self._workout.phases)
        if total_duration_seconds >= 120:
            scheduled.append(
                (
                    total_duration_seconds // 2,
                    LiveCoachingWorkoutHalfway(
                        total_duration_minutes=self._workout.total_duration_minutes,
                    ),
                )
            )

        crossed = [
            (threshold, event)
            for threshold, event in scheduled
            if previous_elapsed_seconds < threshold <= elapsed_seconds
        ]
        crossed.sort(key=lambda item: item[0])
        return tuple(event for _, event in crossed)
