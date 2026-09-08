from domains.person.person import Person
from domains.person.person_repository import PersonRepository


class PersonService:
    """
    Application Service für die Personen des Health Coach.

    Die Persistenz wird über einen Repository-Port injiziert.
    Der Service kennt dadurch weder SQLAlchemy noch SQLite.
    """

    def __init__(self, repository: PersonRepository) -> None:
        self._repository = repository

    def get_persons(self) -> list[Person]:
        return self._repository.get_all()

    def get_person(self, person_id: int) -> Person | None:
        return self._repository.get(person_id)
