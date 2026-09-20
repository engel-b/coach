from dataclasses import dataclass, replace
from datetime import UTC, datetime
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

from features.workout.domain.video import WorkoutVideo
from features.workout.domain.video_path import validate_workout_video_path
from features.workout.domain.video_repository import WorkoutVideoRepository


@dataclass(frozen=True)
class VideoCatalogSyncResult:
    added: int = 0
    reactivated: int = 0
    deactivated: int = 0


class VideoCatalogSyncService:
    def __init__(
        self,
        *,
        repository: WorkoutVideoRepository,
        video_directory: Path,
    ) -> None:
        self._repository = repository
        self._video_directory = video_directory

    @property
    def video_directory(self) -> Path:
        return self._video_directory

    def sync(self) -> VideoCatalogSyncResult:
        if not self._video_directory.is_dir():
            return VideoCatalogSyncResult()

        existing = self._repository.get_all(active_only=False)
        by_path = {video.file_path: video for video in existing}
        discovered_paths = {
            path.relative_to(self._video_directory).as_posix()
            for path in self._video_directory.rglob("*")
            if path.is_file() and path.suffix.lower() == ".mp4"
        }

        added = reactivated = deactivated = 0

        for file_path in sorted(discovered_paths):
            validate_workout_video_path(file_path)
            known = by_path.get(file_path)
            if known is None:
                path = Path(file_path)
                self._repository.save(
                    WorkoutVideo(
                        id=str(uuid5(NAMESPACE_URL, f"health-coach-video:{file_path}")),
                        title=path.stem.replace("_", " ").replace("-", " ").strip().title(),
                        file_path=file_path,
                        created_at=datetime.now(UTC),
                    )
                )
                added += 1
            elif not known.active:
                self._repository.save(replace(known, active=True))
                reactivated += 1

        for video in existing:
            if video.active and video.file_path not in discovered_paths:
                self._repository.save(replace(video, active=False))
                deactivated += 1

        return VideoCatalogSyncResult(
            added=added,
            reactivated=reactivated,
            deactivated=deactivated,
        )
