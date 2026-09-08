from typing import Protocol

from features.workout.domain.session import WorkoutSession


class WorkoutRepository(Protocol):
    """
    Persistenz-Port für WorkoutSessions.

    Heute RAM, später PostgreSQL.
    """

    def save(self, workout: WorkoutSession) -> None: ...

    def get(self, workout_id: str) -> WorkoutSession | None: ...

    def get_for_person(
        self,
        person_id: int,
        *,
        limit: int = 20,
    ) -> list[WorkoutSession]: ...
