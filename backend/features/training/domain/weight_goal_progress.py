from dataclasses import dataclass
from enum import StrEnum


class WeightGoalStatus(StrEnum):
    NO_GOAL = "no_goal"
    NO_CURRENT_WEIGHT = "no_current_weight"
    ABOVE_TARGET = "above_target"
    AT_TARGET = "at_target"
    BELOW_TARGET = "below_target"


@dataclass(frozen=True)
class WeightGoalProgress:
    """
    Deskriptiver Fortschritt relativ zu einem hinterlegten Zielgewicht.

    Das Objekt bewertet ausdrücklich nicht, ob eine Abnahmerate gesund,
    optimal oder zu langsam/schnell ist. Es beschreibt nur den aktuellen
    Abstand zum persönlichen Zielgewicht.
    """

    status: WeightGoalStatus
    current_weight_kg: float | None
    target_weight_kg: float | None
    remaining_kg: float | None
