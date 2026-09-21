from collections.abc import Callable

from sqlalchemy import select
from sqlalchemy.orm import Session

from adapters.persistence.database import create_session
from features.workout.domain.video import WorkoutVideo
from features.workout.persistence.workout_video_model import WorkoutVideoModel


class SqlAlchemyWorkoutVideoRepository:
    """
    SQLAlchemy-Persistenz für den Workout-Video-Katalog.

    Standardmäßig wird die produktive Session-Factory verwendet.

    Für Tests kann eine andere Session-Factory injiziert werden.
    Dadurch bleibt das Repository unabhängig von einer konkreten
    Datenbankinstanz.

    Java-Vergleich:
    Ähnlich wie Constructor Injection eines EntityManagers bzw.
    einer EntityManagerFactory.
    """

    def __init__(
        self,
        session_factory: Callable[[], Session] = create_session,
    ) -> None:
        self._session_factory = session_factory

    def save(
        self,
        video: WorkoutVideo,
    ) -> None:
        with self._session_factory() as session:
            existing = session.get(
                WorkoutVideoModel,
                video.id,
            )

            if existing is None:
                model = WorkoutVideoModel(
                    id=video.id,
                    title=video.title,
                    description=video.description,
                    file_path=video.file_path,
                    duration_seconds=video.duration_seconds,
                    active=video.active,
                    created_at=video.created_at,
                )

                session.add(model)

            else:
                existing.title = video.title
                existing.description = video.description
                existing.file_path = video.file_path
                existing.duration_seconds = video.duration_seconds
                existing.active = video.active

            session.commit()

    def get(
        self,
        video_id: str,
    ) -> WorkoutVideo | None:
        with self._session_factory() as session:
            model = session.get(
                WorkoutVideoModel,
                video_id,
            )

            if model is None:
                return None

            return self._to_domain(model)

    def get_by_file_path(self, file_path: str) -> WorkoutVideo | None:
        with self._session_factory() as session:
            model = session.scalar(
                select(WorkoutVideoModel).where(WorkoutVideoModel.file_path == file_path)
            )
            return None if model is None else self._to_domain(model)

    def get_all(
        self,
        *,
        active_only: bool = True,
    ) -> list[WorkoutVideo]:
        with self._session_factory() as session:
            statement = select(WorkoutVideoModel)

            if active_only:
                statement = statement.where(WorkoutVideoModel.active.is_(True))

            statement = statement.order_by(WorkoutVideoModel.title.asc())

            models = session.scalars(statement).all()

            return [self._to_domain(model) for model in models]

    @staticmethod
    def _to_domain(
        model: WorkoutVideoModel,
    ) -> WorkoutVideo:
        return WorkoutVideo(
            id=model.id,
            title=model.title,
            description=model.description,
            file_path=model.file_path,
            duration_seconds=model.duration_seconds,
            active=model.active,
            created_at=model.created_at,
        )
