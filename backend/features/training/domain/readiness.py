from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class SleepStatus(StrEnum):
    UNKNOWN = "unknown"
    ADEQUATE = "adequate"
    SHORT = "short"


class DailyActivityStatus(StrEnum):
    UNKNOWN = "unknown"
    NORMAL = "normal"
    HIGH = "high"


class RecentTrainingLoadStatus(StrEnum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"


@dataclass(frozen=True)
class RecentTrainingSession:
    """Feature-neutraler Verlaufseintrag für die Readiness-Bewertung."""

    started_at: datetime
    active_minutes: float


@dataclass(frozen=True)
class ReadinessContext:
    """
    Normalisierte Pre-Workout-Signale.

    Die Werte sind Coaching-Hinweise und keine medizinische Bewertung.
    In der ersten Version können belastende Signale die empfohlene Dauer
    begrenzen, aber niemals wegen zu wenig Aktivität die Belastung erhöhen.
    """

    sleep_status: SleepStatus
    daily_activity_status: DailyActivityStatus
    recent_training_load_status: RecentTrainingLoadStatus
    recent_training_minutes: float
    recent_workout_count: int
    max_duration_minutes: int | None
