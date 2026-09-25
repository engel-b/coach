from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from features.training.domain.recommendation import WorkoutPhase, WorkoutType
from features.workout.domain.adaptive_evaluation import WorkoutExpectation
from features.workout.domain.bike_summary import WorkoutBikeSummary
from features.workout.domain.heart_rate_summary import WorkoutHeartRateSummary

DEFAULT_VIDEO_ID = "Lqhq5UQ-U8A"


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
    workout_type: WorkoutType | None = None

    elapsed_seconds: int = 0
    distance_m: int = 0

    video_id: str = DEFAULT_VIDEO_ID
    video_position_seconds: float = 0.0

    completed_at: datetime | None = None
    heart_rate_summary: WorkoutHeartRateSummary | None = None
    bike_summary: WorkoutBikeSummary | None = None
    expectation: WorkoutExpectation | None = None
