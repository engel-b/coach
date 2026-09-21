from dataclasses import dataclass
from enum import StrEnum


class HeartRateZoneStatus(StrEnum):
    """Position der aktuellen Herzfrequenz relativ zum Zielbereich."""

    BELOW_TARGET = "below_target"
    IN_TARGET = "in_target"
    ABOVE_TARGET = "above_target"


class CoachingAction(StrEnum):
    """Fachliche Aktion des Live Coaches, noch ohne Sprachformulierung."""

    NONE = "none"
    INCREASE_INTENSITY = "increase_intensity"
    REDUCE_INTENSITY = "reduce_intensity"


@dataclass(frozen=True)
class LiveCoachingContext:
    """
    Eingabedaten für eine einzelne Live-Coaching-Entscheidung.

    outside_target_seconds beschreibt, wie lange die Herzfrequenz bereits
    ununterbrochen außerhalb des aktuellen Zielbereichs liegt. Die Ermittlung
    dieses Verlaufs gehört bewusst nicht in diese erste, reine Entscheidungslogik.
    """

    heart_rate_bpm: int
    target_min_bpm: int
    target_max_bpm: int
    outside_target_seconds: float


@dataclass(frozen=True)
class LiveCoachingDecision:
    """Ergebnis der fachlichen Live-Coaching-Bewertung."""

    action: CoachingAction
    zone_status: HeartRateZoneStatus
    heart_rate_bpm: int
    target_min_bpm: int
    target_max_bpm: int
    outside_target_seconds: float
    reason: str


@dataclass(frozen=True)
class LiveCoachingPhaseStarted:
    """Fachliches Ereignis für den Beginn einer neuen Workout-Phase."""

    phase_index: int
    phase_type: str
    duration_minutes: int
    target_min_bpm: int
    target_max_bpm: int
    is_final_phase: bool = False


@dataclass(frozen=True)
class LiveCoachingPhaseEnding:
    """Fachliches Ereignis kurz vor dem Ende der aktuellen Workout-Phase."""

    phase_index: int
    phase_type: str
    remaining_seconds: int


@dataclass(frozen=True)
class LiveCoachingWorkoutHalfway:
    """Fachliches Ereignis beim Erreichen der Workout-Halbzeit."""

    total_duration_minutes: int


LiveCoachingStructureEvent = (
    LiveCoachingPhaseStarted | LiveCoachingPhaseEnding | LiveCoachingWorkoutHalfway
)


@dataclass(frozen=True)
class LiveCoachingRules:
    """Konfigurierbare Regeln für die erste Live-Coaching-Version."""

    deviation_seconds_before_action: float = 20.0
    target_tolerance_bpm: int = 0
