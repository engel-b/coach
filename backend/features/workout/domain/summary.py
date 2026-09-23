from dataclasses import dataclass

from features.workout.domain.heart_rate_summary import WorkoutHeartRateSummary
from features.workout.domain.session import WorkoutStatus


@dataclass(frozen=True)
class WorkoutSummary:
    """
    Fachliche Zusammenfassung eines Workouts.

    Neben Zeit und Distanz kann die Zusammenfassung eine kompakte
    Herzfrequenz-Auswertung der Hauptphase enthalten. Weitere
    Telemetrie-Auswertungen wie Leistung oder Kadenz können später
    ergänzt werden.
    """

    planned_seconds: int
    elapsed_seconds: int
    distance_m: int
    completion_percent: int
    status: WorkoutStatus
    heart_rate_summary: WorkoutHeartRateSummary | None = None


def create_workout_summary(
    *,
    total_duration_minutes: int,
    elapsed_seconds: int,
    distance_m: int,
    status: WorkoutStatus,
    heart_rate_summary: WorkoutHeartRateSummary | None = None,
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
        distance_m=distance_m,
        completion_percent=completion_percent,
        status=status,
        heart_rate_summary=heart_rate_summary,
    )
