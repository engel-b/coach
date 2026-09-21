from collections.abc import Callable
from datetime import date

from sqlalchemy.orm import Session

from adapters.persistence.database import create_session
from features.person.domain.person import Person
from features.person.domain.person_profile_writer import PersonProfileWriter
from features.person.domain.profile import PersonProfile, TrainingGoal
from features.person.persistence.person_model import PersonModel, PersonProfileModel


class SqlAlchemyPersonProfileWriter(PersonProfileWriter):
    def __init__(
        self,
        session_factory: Callable[[], Session] = create_session,
    ) -> None:
        self._session_factory = session_factory

    def create(
        self,
        *,
        display_name: str,
        date_of_birth: date,
        height_cm: int,
        training_goal: TrainingGoal,
        max_heart_rate_bpm: int | None,
        resting_heart_rate_bpm: int | None,
        start_weight_kg: float | None,
        target_weight_kg: float | None,
    ) -> tuple[Person, PersonProfile]:
        """Legt Person und Profil gemeinsam in einer Transaktion an."""

        with self._session_factory() as session:
            person_model = PersonModel(
                display_name=display_name,
            )

            session.add(person_model)
            session.flush()

            # flush() führt den INSERT aus, ohne die Transaktion
            # abzuschließen. Die automatisch erzeugte ID ist nun verfügbar.
            person_id = person_model.id

            profile_model = PersonProfileModel(
                person_id=person_id,
                date_of_birth=date_of_birth,
                height_cm=height_cm,
                training_goal=training_goal.value,
                max_heart_rate_bpm=max_heart_rate_bpm,
                resting_heart_rate_bpm=resting_heart_rate_bpm,
                start_weight_kg=start_weight_kg,
                target_weight_kg=target_weight_kg,
            )

            session.add(profile_model)
            session.commit()

            return (
                Person(
                    id=person_id,
                    display_name=display_name,
                ),
                PersonProfile(
                    person_id=person_id,
                    date_of_birth=date_of_birth,
                    height_cm=height_cm,
                    training_goal=training_goal,
                    max_heart_rate_bpm=max_heart_rate_bpm,
                    resting_heart_rate_bpm=resting_heart_rate_bpm,
                    start_weight_kg=start_weight_kg,
                    target_weight_kg=target_weight_kg,
                ),
            )

    def save(
        self,
        person: Person,
        profile: PersonProfile,
    ) -> tuple[Person, PersonProfile]:
        """Aktualisiert Person und Profil atomar."""

        if person.id != profile.person_id:
            raise ValueError("Person ID and profile person ID must match.")

        with self._session_factory() as session:
            person_model = session.get(PersonModel, person.id)

            if person_model is None:
                raise ValueError(f"Person not found: {person.id}")

            profile_model = session.get(
                PersonProfileModel,
                profile.person_id,
            )

            person_model.display_name = person.display_name

            if profile_model is None:
                profile_model = PersonProfileModel(
                    person_id=profile.person_id,
                    date_of_birth=profile.date_of_birth,
                    height_cm=profile.height_cm,
                    training_goal=profile.training_goal.value,
                    max_heart_rate_bpm=profile.max_heart_rate_bpm,
                    resting_heart_rate_bpm=profile.resting_heart_rate_bpm,
                    start_weight_kg=profile.start_weight_kg,
                    target_weight_kg=profile.target_weight_kg,
                )
                session.add(profile_model)
            else:
                profile_model.date_of_birth = profile.date_of_birth
                profile_model.height_cm = profile.height_cm
                profile_model.training_goal = profile.training_goal.value
                profile_model.max_heart_rate_bpm = profile.max_heart_rate_bpm
                profile_model.resting_heart_rate_bpm = profile.resting_heart_rate_bpm
                profile_model.start_weight_kg = profile.start_weight_kg
                profile_model.target_weight_kg = profile.target_weight_kg

            # Beide Änderungen werden mit einem Commit gespeichert.
            # Bei einer Ausnahme vor dem Commit schließt die Session
            # ohne die unvollständige Transaktion zu übernehmen.
            session.commit()

        return person, profile
