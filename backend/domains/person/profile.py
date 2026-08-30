from dataclasses import dataclass
from datetime import date
from enum import StrEnum


class TrainingGoal(StrEnum):
    """
    Primäres Trainingsziel einer Person.

    Später können wir das Modell erweitern, z. B. um mehrere
    parallele Ziele oder Prioritäten.
    """

    GENERAL_FITNESS = "general_fitness"
    WEIGHT_LOSS = "weight_loss"
    ENDURANCE = "endurance"


@dataclass(frozen=True)
class PersonProfile:
    """
    Trainingsrelevante Stammdaten einer Person.

    Das aktuelle Gewicht gehört bewusst nicht hier hinein:
    Gewicht ist ein zeitabhängiger Messwert und wird später
    als eigene Historie gespeichert.
    """

    person_id: int
    date_of_birth: date
    height_cm: int
    training_goal: TrainingGoal

    # Falls die tatsächliche HFmax bekannt bzw. später ermittelt wurde,
    # verwenden wir diese statt einer altersbasierten Schätzung.
    max_heart_rate_bpm: int | None = None
