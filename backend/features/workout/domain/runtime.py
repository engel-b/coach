from enum import StrEnum


class WorkoutRuntimeState(StrEnum):
    """Nicht persistierter Laufzeitzustand eines aktiven Workouts."""

    RUNNING = "running"
    PAUSED = "paused"
    FINISH_WINDOW = "finish_window"
    OVERTIME = "overtime"
