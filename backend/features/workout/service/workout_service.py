from dataclasses import replace
from datetime import UTC, datetime
from uuid import uuid4

from features.training.domain.load_response import LoadResponseStatus
from features.training.domain.recommendation import TrainingRecommendation
from features.workout.domain.adaptive_evaluation import WorkoutExpectation
from features.workout.domain.bike_summary import WorkoutBikeSummary
from features.workout.domain.heart_rate_summary import WorkoutHeartRateSummary
from features.workout.domain.repository import WorkoutRepository
from features.workout.domain.session import DEFAULT_VIDEO_ID, WorkoutSession, WorkoutStatus
from features.workout.domain.summary import WorkoutSummary, create_workout_summary
from features.workout.domain.video_repository import WorkoutVideoRepository


class InvalidWorkoutVideoError(ValueError):
    pass


class WorkoutNotFoundError(ValueError):
    pass


class WorkoutAlreadyFinishedError(ValueError):
    pass


class InvalidWorkoutDurationError(ValueError):
    pass


class WorkoutService:
    """
    Application Service für konkret laufende Trainingseinheiten.
    """

    def __init__(
        self,
        repository: WorkoutRepository,
        video_repository: WorkoutVideoRepository | None = None,
    ) -> None:
        self._repository = repository
        self._video_repository = video_repository

    def start(
        self,
        *,
        person_id: int,
        recommendation: TrainingRecommendation,
        video_id: str | None = None,
    ) -> WorkoutSession:
        previous_workouts = self._repository.get_for_person(
            person_id,
            limit=1,
        )

        previous_workout = previous_workouts[0] if previous_workouts else None

        if video_id is not None:
            if self._video_repository is None:
                raise RuntimeError("Workout video repository is not configured")

            selected_video = self._video_repository.get(video_id)

            if selected_video is None or not selected_video.active:
                raise InvalidWorkoutVideoError(f"Workout video is not available: {video_id}")

            selected_video_id = selected_video.id
        else:
            selected_video_id = (
                previous_workout.video_id if previous_workout is not None else DEFAULT_VIDEO_ID
            )

        video_position_seconds = (
            previous_workout.video_position_seconds
            if previous_workout is not None and previous_workout.video_id == selected_video_id
            else 0.0
        )

        workout = WorkoutSession(
            id=str(uuid4()),
            person_id=person_id,
            started_at=datetime.now(UTC),
            status=WorkoutStatus.RUNNING,
            phases=recommendation.phases,
            total_duration_minutes=recommendation.total_duration_minutes,
            workout_type=recommendation.workout_type,
            expectation=(
                WorkoutExpectation(
                    workout_type=recommendation.workout_type,
                    historical_response=(
                        recommendation.load_response.status
                        if recommendation.load_response.workout_type is recommendation.workout_type
                        else LoadResponseStatus.INSUFFICIENT_DATA
                    ),
                    comparable_workout_count=(
                        recommendation.load_response.comparable_workout_count
                        if recommendation.load_response.workout_type is recommendation.workout_type
                        else 0
                    ),
                    median_target_position_percent=(
                        recommendation.heart_rate_history.median_target_position_percent
                        if recommendation.heart_rate_history
                        and recommendation.load_response.workout_type is recommendation.workout_type
                        else None
                    ),
                    median_power_w=(
                        recommendation.load_response.median_power_w
                        if recommendation.load_response.workout_type is recommendation.workout_type
                        else None
                    ),
                )
                if recommendation.load_response
                else None
            ),
            video_id=selected_video_id,
            video_position_seconds=video_position_seconds,
        )

        self._repository.save(workout)

        return workout

    def checkpoint(
        self,
        workout_id: str,
        *,
        elapsed_seconds: int,
        distance_m: int,
        video_position_seconds: float,
    ) -> WorkoutSession:
        workout = self._get_running_workout(workout_id)

        self._validate_elapsed_seconds(elapsed_seconds)
        self._validate_distance_m(distance_m)

        if video_position_seconds < 0:
            raise ValueError("Video position seconds must not be negative")

        updated = replace(
            workout,
            elapsed_seconds=elapsed_seconds,
            distance_m=distance_m,
            video_position_seconds=video_position_seconds,
        )

        self._repository.save(updated)

        return updated

    def finish(
        self,
        workout_id: str,
        *,
        elapsed_seconds: int,
        distance_m: int,
        heart_rate_summary: WorkoutHeartRateSummary | None = None,
        bike_summary: WorkoutBikeSummary | None = None,
    ) -> WorkoutSession:
        workout = self._get_running_workout(workout_id)

        self._validate_elapsed_seconds(elapsed_seconds)
        self._validate_distance_m(distance_m)

        planned_seconds = workout.total_duration_minutes * 60

        status = (
            WorkoutStatus.COMPLETED if elapsed_seconds >= planned_seconds else WorkoutStatus.ABORTED
        )

        finished = replace(
            workout,
            status=status,
            elapsed_seconds=elapsed_seconds,
            distance_m=distance_m,
            completed_at=datetime.now(UTC),
            heart_rate_summary=heart_rate_summary,
            bike_summary=bike_summary,
        )

        self._repository.save(finished)

        return finished

    def get(
        self,
        workout_id: str,
    ) -> WorkoutSession | None:
        return self._repository.get(workout_id)

    def get_summary(
        self,
        workout_id: str,
    ) -> WorkoutSummary:
        workout = self._repository.get(workout_id)

        if workout is None:
            raise WorkoutNotFoundError(f"Workout {workout_id} not found")

        return create_workout_summary(
            total_duration_minutes=(workout.total_duration_minutes),
            elapsed_seconds=(workout.elapsed_seconds),
            distance_m=(workout.distance_m),
            status=workout.status,
            heart_rate_summary=workout.heart_rate_summary,
            bike_summary=workout.bike_summary,
            expectation=workout.expectation,
        )

    def _get_running_workout(
        self,
        workout_id: str,
    ) -> WorkoutSession:
        workout = self._repository.get(workout_id)

        if workout is None:
            raise WorkoutNotFoundError(f"Workout {workout_id} not found")

        if workout.status != WorkoutStatus.RUNNING:
            raise WorkoutAlreadyFinishedError(f"Workout {workout_id} is not running")

        return workout

    @staticmethod
    def _validate_elapsed_seconds(
        elapsed_seconds: int,
    ) -> None:
        if elapsed_seconds < 0:
            raise InvalidWorkoutDurationError("Elapsed seconds must not be negative")

    @staticmethod
    def _validate_distance_m(
        distance_m: int,
    ) -> None:
        if distance_m < 0:
            raise ValueError("Distance meters must not be negative")

    def get_for_person(
        self,
        person_id: int,
        *,
        limit: int = 20,
    ) -> list[WorkoutSession]:
        return self._repository.get_for_person(
            person_id,
            limit=limit,
        )
