from sqlalchemy import select
from sqlalchemy.orm import selectinload

from adapters.persistence.database import create_session
from features.training.domain.recommendation import (
    WorkoutPhase,
    WorkoutPhaseType,
    WorkoutType,
)
from features.workout.domain.heart_rate_summary import WorkoutHeartRateSummary
from features.workout.domain.session import (
    WorkoutSession,
    WorkoutStatus,
)
from features.workout.persistence.workout_model import (
    WorkoutModel,
    WorkoutPhaseModel,
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
                    workout_type=(
                        workout.workout_type.value if workout.workout_type is not None else None
                    ),
                    elapsed_seconds=workout.elapsed_seconds,
                    distance_m=workout.distance_m,
                    video_id=workout.video_id,
                    video_position_seconds=workout.video_position_seconds,
                    completed_at=workout.completed_at,
                    heart_rate_sample_count=(
                        workout.heart_rate_summary.sample_count
                        if workout.heart_rate_summary is not None
                        else None
                    ),
                    heart_rate_average_bpm=(
                        workout.heart_rate_summary.average_bpm
                        if workout.heart_rate_summary is not None
                        else None
                    ),
                    heart_rate_max_bpm=(
                        workout.heart_rate_summary.max_bpm
                        if workout.heart_rate_summary is not None
                        else None
                    ),
                    heart_rate_below_target_percent=(
                        workout.heart_rate_summary.below_target_percent
                        if workout.heart_rate_summary is not None
                        else None
                    ),
                    heart_rate_in_target_percent=(
                        workout.heart_rate_summary.in_target_percent
                        if workout.heart_rate_summary is not None
                        else None
                    ),
                    heart_rate_above_target_percent=(
                        workout.heart_rate_summary.above_target_percent
                        if workout.heart_rate_summary is not None
                        else None
                    ),
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
                existing.workout_type = (
                    workout.workout_type.value if workout.workout_type is not None else None
                )
                existing.elapsed_seconds = workout.elapsed_seconds
                existing.distance_m = workout.distance_m
                existing.video_id = workout.video_id
                existing.video_position_seconds = workout.video_position_seconds
                existing.completed_at = workout.completed_at
                if workout.heart_rate_summary is not None:
                    existing.heart_rate_sample_count = workout.heart_rate_summary.sample_count
                    existing.heart_rate_average_bpm = workout.heart_rate_summary.average_bpm
                    existing.heart_rate_max_bpm = workout.heart_rate_summary.max_bpm
                    existing.heart_rate_below_target_percent = (
                        workout.heart_rate_summary.below_target_percent
                    )
                    existing.heart_rate_in_target_percent = (
                        workout.heart_rate_summary.in_target_percent
                    )
                    existing.heart_rate_above_target_percent = (
                        workout.heart_rate_summary.above_target_percent
                    )

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
            total_duration_minutes=model.total_duration_minutes,
            workout_type=(
                WorkoutType(model.workout_type) if model.workout_type is not None else None
            ),
            elapsed_seconds=model.elapsed_seconds,
            distance_m=model.distance_m,
            video_id=model.video_id,
            video_position_seconds=model.video_position_seconds,
            completed_at=model.completed_at,
            heart_rate_summary=(
                WorkoutHeartRateSummary(
                    sample_count=model.heart_rate_sample_count,
                    average_bpm=model.heart_rate_average_bpm,
                    max_bpm=model.heart_rate_max_bpm,
                    below_target_percent=model.heart_rate_below_target_percent,
                    in_target_percent=model.heart_rate_in_target_percent,
                    above_target_percent=model.heart_rate_above_target_percent,
                )
                if model.heart_rate_sample_count is not None
                and model.heart_rate_average_bpm is not None
                and model.heart_rate_max_bpm is not None
                and model.heart_rate_below_target_percent is not None
                and model.heart_rate_in_target_percent is not None
                and model.heart_rate_above_target_percent is not None
                else None
            ),
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
