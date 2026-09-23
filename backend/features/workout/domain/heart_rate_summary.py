from dataclasses import dataclass


@dataclass(frozen=True)
class WorkoutHeartRateSummary:
    """Kompakte Herzfrequenz-Auswertung der Hauptphase eines Workouts."""

    sample_count: int
    average_bpm: int
    max_bpm: int
    below_target_percent: int
    in_target_percent: int
    above_target_percent: int
