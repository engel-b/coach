from features.check_in.domain.check_in import CheckIn


class InMemoryCheckInRepository:
    """
    Temporäre Repository-Implementierung.

    Die Daten gehen beim Neustart des Backends verloren.

    Dieser Adapter wird später durch ein PostgreSQL-Repository ersetzt.
    """

    def __init__(self) -> None:
        self._check_ins: list[CheckIn] = []

    def save(self, check_in: CheckIn) -> None:
        self._check_ins.append(check_in)

    def get_latest_for_person(
        self,
        person_id: int,
    ) -> CheckIn | None:
        matching = [check_in for check_in in self._check_ins if check_in.person_id == person_id]

        if not matching:
            return None

        return max(
            matching,
            key=lambda check_in: check_in.timestamp,
        )
