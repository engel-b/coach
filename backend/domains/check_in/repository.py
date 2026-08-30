from typing import Protocol

from domains.check_in.check_in import CheckIn


class CheckInRepository(Protocol):
    """
    Port für die Speicherung von Check-ins.

    Die Domain/Application-Schicht weiß dadurch nicht,
    ob die Daten in RAM, PostgreSQL oder anderswo liegen.

    Java-Vergleich:
        ungefähr ein Repository-Interface.
    """

    def save(self, check_in: CheckIn) -> None: ...

    def get_latest_for_person(
        self,
        person_id: int,
    ) -> CheckIn | None: ...
