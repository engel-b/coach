from collections.abc import Callable
from datetime import date

from domains.person.profile import TrainingGoal
from sqlalchemy.orm import Session

from adapters.persistence.database import create_session
from adapters.persistence.person_model import PersonModel, PersonProfileModel
from domains.person.person import Person
from domains.person.person_profile_writer import PersonProfileWriter
from domains.person.profile import PersonProfile


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
        start_weight_kg: float | None,
        target_weight_kg: float | None,
    ) -> tuple[Person, PersonProfile]:
        with self._session_factory() as session:
            person_model = PersonModel(
                display_name=display_name,
            )

            session.add(person_model)
            session.flush()

            # flush() schreibt den INSERT innerhalb derselben Transaktion,
            # ohne zu committen. Danach steht die automatisch erzeugte ID fest.
            person_id = person_model.id

            profile_model = PersonProfileModel(
                person_id=person_id,
                date_of_birth=date_of_birth,
                height_cm=height_cm,
                training_goal=training_goal.value,
                max_heart_rate_bpm=max_heart_rate_bpm,
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
                    start_weight_kg=start_weight_kg,
                    target_weight_kg=target_weight_kg,
                ),
            )

    def save(
        self,
        person: Person,
        profile: PersonProfile,
    ) -> tuple[Person, PersonProfile]:
        with self._session_factory() as session:
            if person.id != profile.person_id:
                raise ValueError(               "Person ID and profile person ID must match.")
                
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
                    start_weight_kg=profile.start_weight_kg,
                    target_weight_kg=profile.target_weight_kg,
                )
                session.add(profile_model)
            else:
                profile_model.date_of_birth = profile.date_of_birth
                profile_model.height_cm = profile.height_cm
                profile_model.training_goal = profile.training_goal.value
                profile_model.max_heart_rate_bpm = profile.max_heart_rate_bpm
                profile_model.start_weight_kg = profile.start_weight_kg
                profile_model.target_weight_kg = profile.target_weight_kg

            # Ein Commit für beide Änderungen.
            #
            # Schlägt davor etwas fehl, wird beim Schließen der Session
            # keine teilweise Änderung committed.
            session.commit()

        return person, profile