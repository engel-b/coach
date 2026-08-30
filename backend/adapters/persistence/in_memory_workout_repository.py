from domains.workout.session import WorkoutSession


class InMemoryWorkoutRepository:
    """
    Temporäre Speicherung laufender und abgeschlossener Workouts.

    Geht beim Backend-Neustart verloren.
    """

    def __init__(self) -> None:
        self._workouts: dict[str, WorkoutSession] = {}

    def save(self, workout: WorkoutSession) -> None:
        self._workouts[workout.id] = workout

    def get(
        self,
        workout_id: str,
    ) -> WorkoutSession | None:
        return self._workouts.get(workout_id)

    def get_for_person(
        self,
        person_id: int,
        *,
        limit: int = 20,
    ) -> list[WorkoutSession]:
        workouts = [
            workout for workout in self._workouts.values() if workout.person_id == person_id
        ]

        workouts.sort(
            key=lambda workout: workout.started_at,
            reverse=True,
        )

        return workouts[:limit]
