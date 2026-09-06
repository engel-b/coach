from sqlalchemy import select
from sqlalchemy.orm import selectinload

from adapters.persistence.database import create_session
from adapters.persistence.workout_model import (
    WorkoutModel,
    WorkoutPhaseModel,
)
from domains.training.recommendation import (
    WorkoutPhase,
    WorkoutPhaseType,
)
from domains.workout.session import (
    WorkoutSession,
    WorkoutStatus,
)


class SqlAlchemyWorkoutRepository:
    """
    Produktive Persistenz für WorkoutSessions.
    """

    def save(
        self,
        workout: WorkoutSession,
    ) -> None:
        with create_session() as session:
            existing = session.get(
                WorkoutModel,
                workout.id,
            )

            if existing is None:
                model = WorkoutModel(
                    id=workout.id,
                    person_id=workout.person_id,
                    started_at=workout.started_at,
                    status=workout.status.value,
                    total_duration_minutes=(workout.total_duration_minutes),
                    elapsed_seconds=workout.elapsed_seconds,
                    distance_m=workout.distance_m,
                    completed_at=workout.completed_at,
                )

                model.phases = [
                    WorkoutPhaseModel(
                        position=index,
                        phase_type=phase.phase_type.value,
                        duration_minutes=phase.duration_minutes,
                        target_heart_rate_min=(phase.target_heart_rate_min),
                        target_heart_rate_max=(phase.target_heart_rate_max),
                    )
                    for index, phase in enumerate(workout.phases)
                ]

                session.add(model)

            else:
                existing.status = workout.status.value
                existing.elapsed_seconds = workout.elapsed_seconds
                existing.distance_m = workout.distance_m
                existing.completed_at = workout.completed_at

            session.commit()

    def get(
        self,
        workout_id: str,
    ) -> WorkoutSession | None:
        with create_session() as session:
            statement = (
                select(WorkoutModel)
                .options(selectinload(WorkoutModel.phases))
                .where(WorkoutModel.id == workout_id)
            )

            model = session.scalar(statement)

            if model is None:
                return None

            return self._to_domain(model)

    def get_for_person(
        self,
        person_id: int,
        *,
        limit: int = 20,
    ) -> list[WorkoutSession]:
        with create_session() as session:
            statement = (
                select(WorkoutModel)
                .options(selectinload(WorkoutModel.phases))
                .where(WorkoutModel.person_id == person_id)
                .order_by(WorkoutModel.started_at.desc())
                .limit(limit)
            )

            models = session.scalars(statement).all()

            return [self._to_domain(model) for model in models]

    @staticmethod
    def _to_domain(
        model: WorkoutModel,
    ) -> WorkoutSession:
        return WorkoutSession(
            id=model.id,
            person_id=model.person_id,
            started_at=model.started_at,
            status=WorkoutStatus(model.status),
            total_duration_minutes=(model.total_duration_minutes),
            elapsed_seconds=(model.elapsed_seconds),
            distance_m=(model.distance_m),
            completed_at=model.completed_at,
            phases=tuple(
                WorkoutPhase(
                    phase_type=(WorkoutPhaseType(phase.phase_type)),
                    duration_minutes=(phase.duration_minutes),
                    target_heart_rate_min=(phase.target_heart_rate_min),
                    target_heart_rate_max=(phase.target_heart_rate_max),
                )
                for phase in sorted(
                    model.phases,
                    key=lambda phase: phase.position,
                )
            ),
        )
