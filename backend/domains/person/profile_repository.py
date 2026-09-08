from typing import Protocol

from domains.person.profile import PersonProfile


class PersonProfileRepository(Protocol):
    def get(self, person_id: int) -> PersonProfile | None: ...

    def save(self, profile: PersonProfile) -> PersonProfile: ...
