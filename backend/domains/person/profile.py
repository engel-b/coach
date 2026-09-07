from dataclasses import dataclass
from datetime import date
from enum import StrEnum


class TrainingGoal(StrEnum):
    """
    Primäres Trainingsziel einer Person.

    Die bisherigen Werte bleiben erhalten, damit bestehende
    Daten und API-Verträge kompatibel bleiben.
    """

    GENERAL_FITNESS = "general_fitness"
    WEIGHT_LOSS = "weight_loss"
    ENDURANCE = "endurance"
    MUSCLE_GAIN = "muscle_gain"


@dataclass(frozen=True)
class PersonProfile:
    """
    Trainingsrelevante Stammdaten einer Person.

    Das aktuelle Gewicht gehört bewusst nicht hier hinein:
    Es ist ein zeitabhängiger Messwert und wird im Check-in
    beziehungsweise in der Messwerthistorie gespeichert.

    Start- und Zielgewicht beschreiben dagegen das langfristige
    Trainingsziel und gehören deshalb zum Profil.
    """

    person_id: int
    date_of_birth: date
    height_cm: int
    training_goal: TrainingGoal

    # Falls die tatsächliche HFmax bekannt bzw. später ermittelt wurde,
    # verwenden wir diese statt einer altersbasierten Schätzung.
    max_heart_rate_bpm: int | None = None

    # Zielbezogene Stammdaten. Bei Abnehmen werden beide benötigt.
    start_weight_kg: float | None = None
    target_weight_kg: float | None = None