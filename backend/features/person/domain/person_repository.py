from typing import Protocol

from domains.person.person import Person


class PersonRepository(Protocol):
    def get_all(self) -> list[Person]: ...

    def get(self, person_id: int) -> Person | None: ...

    def save(self, person: Person) -> Person: ...
