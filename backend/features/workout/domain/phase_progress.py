from dataclasses import dataclass

from features.training.domain.recommendation import WorkoutPhase
from features.workout.domain.session import WorkoutSession


@dataclass(frozen=True)
class WorkoutPhaseProgress:
    """
    Aktuelle Position innerhalb eines laufenden Workouts.

    phase_elapsed_seconds:
        Bereits absolvierte aktive Zeit innerhalb der aktuellen Phase.

    phase_remaining_seconds:
        Noch verbleibende aktive Zeit innerhalb der aktuellen Phase.
    """

    phase: WorkoutPhase
    phase_index: int
    phase_elapsed_seconds: int
    phase_remaining_seconds: int


def get_current_phase(
    workout: WorkoutSession,
    *,
    elapsed_seconds: int,
) -> WorkoutPhaseProgress | None:
    """
    Bestimmt anhand der aktiven Trainingszeit die aktuelle Workout-Phase.

    Pausenzeiten sind hier bewusst irrelevant, weil elapsed_seconds
    bereits nur die aktive Trainingszeit enthält.
    """

    if elapsed_seconds < 0:
        raise ValueError("elapsed_seconds must not be negative")

    phase_start_seconds = 0

    for index, phase in enumerate(workout.phases):
        phase_duration_seconds = phase.duration_minutes * 60
        phase_end_seconds = phase_start_seconds + phase_duration_seconds

        if elapsed_seconds < phase_end_seconds:
            phase_elapsed_seconds = elapsed_seconds - phase_start_seconds

            return WorkoutPhaseProgress(
                phase=phase,
                phase_index=index,
                phase_elapsed_seconds=phase_elapsed_seconds,
                phase_remaining_seconds=(phase_duration_seconds - phase_elapsed_seconds),
            )

        phase_start_seconds = phase_end_seconds

    return None
