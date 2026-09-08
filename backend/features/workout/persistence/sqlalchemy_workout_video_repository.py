from sqlalchemy import select

from adapters.persistence.database import create_session
from features.workout.domain.video import WorkoutVideo
from features.workout.persistence.workout_video_model import WorkoutVideoModel


class SqlAlchemyWorkoutVideoRepository:
    """
    Produktive Persistenz für den Workout-Video-Katalog.
    """

    def save(
        self,
        video: WorkoutVideo,
    ) -> None:
        with create_session() as session:
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
        with create_session() as session:
            model = session.get(
                WorkoutVideoModel,
                video_id,
            )

            if model is None:
                return None

            return self._to_domain(model)

    def get_all(
        self,
        *,
        active_only: bool = True,
    ) -> list[WorkoutVideo]:
        with create_session() as session:
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
