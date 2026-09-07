from domains.person.person import Person
from domains.person.person_profile_writer import PersonProfileWriter
from domains.person.person_repository import PersonRepository
from domains.person.profile import PersonProfile


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

        return self._profile_writer.save(
            updated_person,
            profile,
        )