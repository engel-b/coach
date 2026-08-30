from domains.person.person import Person


class PersonService:
    """
    Application Service für die verfügbaren Personen.

    Aktuell sind die Personen statisch konfiguriert.
    Später kommen sie voraussichtlich aus PostgreSQL.
    """

    def __init__(self) -> None:
        self._persons = [
            Person(
                id=1,
                display_name="Björn",
            ),
            Person(
                id=2,
                display_name="Steffi",
            ),
            Person(
                id=3,
                display_name="Person 3",
            ),
            Person(
                id=4,
                display_name="Person 4",
            ),
        ]

    def get_persons(self) -> list[Person]:
        return list(self._persons)

    def get_person(
        self,
        person_id: int,
    ) -> Person | None:
        return next(
            (person for person in self._persons if person.id == person_id),
            None,
        )
