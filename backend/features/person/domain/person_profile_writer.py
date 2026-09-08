from datetime import date
from typing import Protocol

from features.person.domain.person import Person
from features.person.domain.profile import PersonProfile, TrainingGoal


class PersonProfileWriter(Protocol):
    """
    Schreibt Person und Profil als eine atomare fachliche Änderung.

    Entweder werden beide Änderungen gespeichert oder keine.
    """

    def create(
        self,
        *,
        display_name: str,
        date_of_birth: date,
        height_cm: int,
        training_goal: TrainingGoal,
        max_heart_rate_bpm: int | None,
        start_weight_kg: float | None,
        target_weight_kg: float | None,
    ) -> tuple[Person, PersonProfile]: ...

    def save(
        self,
        person: Person,
        profile: PersonProfile,
    ) -> tuple[Person, PersonProfile]: ...
