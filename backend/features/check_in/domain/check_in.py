from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class CheckIn:
    """
    Subjektiver Zustand einer Person vor einer Trainingseinheit.

    Die Skalen reichen jeweils von 1 bis 5.

    Energie / Erholung:
        1 = sehr niedrig
        5 = sehr hoch

    Muskelkater / Stress:
        1 = keiner / sehr niedrig
        5 = sehr stark / sehr hoch

    available_training_minutes beschreibt die Zeit, die die Person
    heute für das Training zur Verfügung hat.
    """

    person_id: int
    timestamp: datetime

    energy: int
    recovery: int
    muscle_soreness: int
    stress: int

    available_training_minutes: int

    current_weight_kg: float | None = None
    sleep_hours: float | None = None
    steps: int | None = None
    resting_heart_rate_bpm: int | None = None
