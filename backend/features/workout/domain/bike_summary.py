from dataclasses import dataclass


@dataclass(frozen=True)
class WorkoutBikeSummary:
    """Kompakte FTMS-Auswertung der Workout-Hauptphase."""

    power_sample_count: int
    average_power_w: int | None
    cadence_sample_count: int
    average_cadence_rpm: float | None
