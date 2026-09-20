from features.workout.domain.video import WorkoutVideo


class InMemoryWorkoutVideoRepository:
    """
    InMemory-Adapter für isolierte Tests.
    """

    def __init__(self) -> None:
        self._videos: dict[str, WorkoutVideo] = {}

    def save(self, video: WorkoutVideo) -> None:
        self._videos[video.id] = video

    def get(self, video_id: str) -> WorkoutVideo | None:
        return self._videos.get(video_id)

    def get_by_file_path(self, file_path: str) -> WorkoutVideo | None:
        return next(
            (video for video in self._videos.values() if video.file_path == file_path), None
        )

    def get_all(
        self,
        *,
        active_only: bool = True,
    ) -> list[WorkoutVideo]:
        videos = list(self._videos.values())

        if active_only:
            videos = [video for video in videos if video.active]

        return sorted(
            videos,
            key=lambda video: video.title,
        )
