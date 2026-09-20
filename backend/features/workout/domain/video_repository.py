from typing import Protocol

from features.workout.domain.video import WorkoutVideo


class WorkoutVideoRepository(Protocol):
    """
    Persistenz-Port für den Video-Katalog.

    Die Anwendung kennt nur diesen Vertrag.
    SQLAlchemy ist ein austauschbarer Adapter.
    """

    def save(self, video: WorkoutVideo) -> None: ...
    def get(self, video_id: str) -> WorkoutVideo | None: ...
    def get_by_file_path(self, file_path: str) -> WorkoutVideo | None: ...
    def get_all(self, *, active_only: bool = True) -> list[WorkoutVideo]: ...
