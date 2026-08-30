from dataclasses import dataclass

from domains.workout.session import WorkoutStatus


@dataclass(frozen=True)
class WorkoutSummary:
    """
    Fachliche Zusammenfassung eines Workouts.

    Später können hier weitere Telemetrie-Auswertungen
    ergänzt werden, zum Beispiel Herzfrequenz, Leistung
    oder Kadenz.
    """

    planned_seconds: int
    elapsed_seconds: int
    completion_percent: int
    status: WorkoutStatus


def create_workout_summary(
    *,
    total_duration_minutes: int,
    elapsed_seconds: int,
    status: WorkoutStatus,
) -> WorkoutSummary:
    """
    Erzeugt die fachliche Auswertung eines Workouts.

    Der Erfüllungsgrad wird auf maximal 100 Prozent
    begrenzt, auch wenn das Workout länger als geplant lief.
    """

    planned_seconds = total_duration_minutes * 60

    if planned_seconds <= 0:
        completion_percent = 0
    else:
        completion_percent = round(elapsed_seconds / planned_seconds * 100)

    completion_percent = min(
        completion_percent,
        100,
    )

    return WorkoutSummary(
        planned_seconds=planned_seconds,
        elapsed_seconds=elapsed_seconds,
        completion_percent=completion_percent,
        status=status,
    )
