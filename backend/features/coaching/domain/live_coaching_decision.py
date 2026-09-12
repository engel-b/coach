from dataclasses import dataclass
from enum import StrEnum


class HeartRateZoneStatus(StrEnum):
    BELOW_TARGET = "below_target"
    IN_TARGET = "in_target"
    ABOVE_TARGET = "above_target"


class CoachingAction(StrEnum):
    NONE = "none"
    INCREASE_INTENSITY = "increase_intensity"
    KEEP_PACE = "keep_pace"
    REDUCE_INTENSITY = "reduce_intensity"


@dataclass(frozen=True)
class LiveCoachingDecision:
    action: CoachingAction
    reason: str
    heart_rate_bpm: int
    target_min_bpm: int
    target_max_bpm: int
