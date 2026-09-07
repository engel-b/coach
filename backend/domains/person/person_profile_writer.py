from typing import Protocol

from domains.person.person import Person
from domains.person.profile import PersonProfile


class PersonProfileWriter(Protocol):
    """
    Schreibt Person und Profil als eine atomare fachliche Änderung.

    Entweder werden beide Änderungen gespeichert oder keine.
    """

    def save(
        self,
        person: Person,
        profile: PersonProfile,
    ) -> tuple[Person, PersonProfile]: ...