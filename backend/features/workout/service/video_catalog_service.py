from dataclasses import dataclass, replace
from datetime import UTC, datetime
from uuid import uuid4

from features.workout.domain.repository import WorkoutRepository
from features.workout.domain.video import WorkoutVideo
from features.workout.domain.video_path import validate_workout_video_path
from features.workout.domain.video_repository import WorkoutVideoRepository


class WorkoutVideoNotFoundError(Exception):
    pass


class WorkoutVideoPathConflictError(ValueError):
    pass


@dataclass(frozen=True)
class WorkoutVideoSelection:
    video: WorkoutVideo
    usage_count: int
    last_used_at: datetime | None
    is_last_used: bool

    @property
    def is_new(self) -> bool:
        return self.usage_count == 0


class VideoCatalogService:
    """
    Anwendungsservice für den Trainingsvideo-Katalog.

    Die API kennt den Service, aber nicht die konkrete
    SQLAlchemy-Implementierung.
    """

    def __init__(
        self,
        repository: WorkoutVideoRepository,
        workout_repository: WorkoutRepository | None = None,
    ) -> None:
        self._repository = repository
        self._workout_repository = workout_repository

    def get_available(self) -> list[WorkoutVideo]:
        return self._repository.get_all(active_only=True)

    def get_all(self) -> list[WorkoutVideo]:
        return self._repository.get_all(active_only=False)

    def get(self, video_id: str) -> WorkoutVideo:
        video = self._repository.get(video_id)
        if video is None:
            raise WorkoutVideoNotFoundError(f"Workout video not found: {video_id}")
        return video

    def create(
        self,
        *,
        title: str,
        file_path: str,
        description: str | None = None,
        duration_seconds: float | None = None,
        active: bool = True,
    ) -> WorkoutVideo:
        file_path = validate_workout_video_path(file_path)
        if self._repository.get_by_file_path(file_path) is not None:
            raise WorkoutVideoPathConflictError(f"Workout video path already exists: {file_path}")
        video = WorkoutVideo(
            id=str(uuid4()),
            title=title.strip(),
            file_path=file_path,
            description=description,
            duration_seconds=duration_seconds,
            active=active,
            created_at=datetime.now(UTC),
        )
        self._repository.save(video)
        return video

    def update(
        self,
        video_id: str,
        *,
        title: str,
        file_path: str,
        description: str | None,
        duration_seconds: float | None,
        active: bool,
    ) -> WorkoutVideo:
        current = self.get(video_id)
        file_path = validate_workout_video_path(file_path)
        conflict = self._repository.get_by_file_path(file_path)
        if conflict is not None and conflict.id != video_id:
            raise WorkoutVideoPathConflictError(f"Workout video path already exists: {file_path}")
        updated = replace(
            current,
            title=title.strip(),
            file_path=file_path,
            description=description,
            duration_seconds=duration_seconds,
            active=active,
        )
        self._repository.save(updated)
        return updated

    def deactivate(self, video_id: str) -> None:
        self._repository.save(replace(self.get(video_id), active=False))

    def get_for_person(self, person_id: int) -> list[WorkoutVideoSelection]:
        if self._workout_repository is None:
            raise RuntimeError("Workout repository is not configured")
        videos = self.get_available()
        workouts = self._workout_repository.get_for_person(person_id, limit=10_000)
        counts: dict[str, int] = {}
        last_used: dict[str, datetime] = {}
        for workout in workouts:
            counts[workout.video_id] = counts.get(workout.video_id, 0) + 1
            previous = last_used.get(workout.video_id)
            if previous is None or workout.started_at > previous:
                last_used[workout.video_id] = workout.started_at
        last_video_id = workouts[0].video_id if workouts else None
        result = [
            WorkoutVideoSelection(
                video=video,
                usage_count=counts.get(video.id, 0),
                last_used_at=last_used.get(video.id),
                is_last_used=video.id == last_video_id,
            )
            for video in videos
        ]
        return sorted(
            result,
            key=lambda item: (item.usage_count, item.video.title.casefold()),
        )
