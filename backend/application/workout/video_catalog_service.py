from domains.workout.video import WorkoutVideo
from domains.workout.video_repository import WorkoutVideoRepository


class WorkoutVideoNotFoundError(Exception):
    pass


class VideoCatalogService:
    """
    Anwendungsservice für den Trainingsvideo-Katalog.

    Die API kennt den Service, aber nicht die konkrete
    SQLAlchemy-Implementierung.
    """

    def __init__(
        self,
        repository: WorkoutVideoRepository,
    ) -> None:
        self._repository = repository

    def get_available(self) -> list[WorkoutVideo]:
        return self._repository.get_all(active_only=True)

    def get(self, video_id: str) -> WorkoutVideo:
        video = self._repository.get(video_id)

        if video is None:
            raise WorkoutVideoNotFoundError(
                f"Workout video not found: {video_id}"
            )

        return video