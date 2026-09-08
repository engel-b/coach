from datetime import date

from domains.person.person import Person
from domains.person.person_profile_writer import PersonProfileWriter
from domains.person.person_repository import PersonRepository
from domains.person.profile import PersonProfile, TrainingGoal
from domains.person.profile_validation import validate_person_profile


class PersonNotFoundError(Exception):
    pass


class PersonManagementService:
    """
    Application Service für Änderungen, die Person und Profil gemeinsam
    betreffen.
    """

    def __init__(
        self,
        person_repository: PersonRepository,
        profile_writer: PersonProfileWriter,
    ) -> None:
        self._person_repository = person_repository
        self._profile_writer = profile_writer

    def create_person(
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
        # Für die Domain-Validierung brauchen wir hier kurz ein Profil.
        # Die endgültige ID entsteht erst in der Datenbank.
        candidate = PersonProfile(
            person_id=0,
            date_of_birth=date_of_birth,
            height_cm=height_cm,
            training_goal=training_goal,
            max_heart_rate_bpm=max_heart_rate_bpm,
            start_weight_kg=start_weight_kg,
            target_weight_kg=target_weight_kg,
        )

        validate_person_profile(candidate)

        return self._profile_writer.create(
            display_name=display_name,
            date_of_birth=date_of_birth,
            height_cm=height_cm,
            training_goal=training_goal,
            max_heart_rate_bpm=max_heart_rate_bpm,
            start_weight_kg=start_weight_kg,
            target_weight_kg=target_weight_kg,
        )

    def update_profile(
        self,
        *,
        person_id: int,
        display_name: str,
        profile: PersonProfile,
    ) -> tuple[Person, PersonProfile]:
        person = self._person_repository.get(person_id)

        if person is None:
            raise PersonNotFoundError(
                f"Person not found: {person_id}"
            )

        updated_person = Person(
            id=person.id,
            display_name=display_name,
        )

        validate_person_profile(profile)

        return self._profile_writer.save(
            updated_person,
            profile,
        )