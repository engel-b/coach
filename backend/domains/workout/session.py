from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from domains.training.recommendation import WorkoutPhase


class WorkoutStatus(StrEnum):
    RUNNING = "running"
    COMPLETED = "completed"
    ABORTED = "aborted"


@dataclass(frozen=True)
class WorkoutSession:
    """
    Eine konkret gestartete Trainingseinheit.

    total_duration_minutes:
        Geplante Trainingsdauer.

    elapsed_seconds:
        Tatsächlich absolvierte aktive Trainingszeit.
        Pausen zählen nicht mit.

    distance_m:
        Tatsächlich während dieses Workouts gefahrene Distanz
        in ganzen Metern.

        Der Wert ist ausdrücklich nicht der absolute
        FTMS-Total-Distance-Zähler des Bikes.
    """

    id: str
    person_id: int
    started_at: datetime
    status: WorkoutStatus
    phases: tuple[WorkoutPhase, ...]
    total_duration_minutes: int

    elapsed_seconds: int = 0
    distance_m: int = 0
    completed_at: datetime | None = None