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
class ReadinessRules:
    """
    Explizite Produktregeln für die Readiness-Bewertung.

    Die Werte sind konservative Coaching-Schwellen und keine medizinischen
    Grenzwerte. Sie liegen als eigenes Value Object vor, damit sie zentral
    testbar, dokumentierbar und später austauschbar bzw. konfigurierbar sind.
    """

    short_sleep_hours: float = 6.0
    high_daily_steps: int = 12_000
    recent_training_window_days: int = 3
    high_recent_training_minutes: float = 90.0
    high_recent_workout_count: int = 3
    caution_duration_cap_minutes: int = 30

    def __post_init__(self) -> None:
        if self.short_sleep_hours <= 0:
            raise ValueError("short_sleep_hours must be positive")
        if self.high_daily_steps <= 0:
            raise ValueError("high_daily_steps must be positive")
        if self.recent_training_window_days < 1:
            raise ValueError("recent_training_window_days must be positive")
        if self.high_recent_training_minutes <= 0:
            raise ValueError("high_recent_training_minutes must be positive")
        if self.high_recent_workout_count < 1:
            raise ValueError("high_recent_workout_count must be positive")
        if self.caution_duration_cap_minutes < 1:
            raise ValueError("caution_duration_cap_minutes must be positive")


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
