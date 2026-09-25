from features.workout.api.contracts.workout import (
    AdaptiveEvaluationResponse,
    WorkoutBikeSummaryResponse,
    WorkoutHeartRateSummaryResponse,
    WorkoutPhaseResponse,
    WorkoutResponse,
    WorkoutSummaryResponse,
)
from features.workout.domain.session import WorkoutSession
from features.workout.domain.summary import WorkoutSummary


def to_workout_response(
    workout: WorkoutSession,
) -> WorkoutResponse:
    """
    Übersetzt unser Domain-Modell in den HTTP-Contract.

    Dadurch bleibt die Domain unabhängig von FastAPI/Pydantic,
    während main.py nicht jedes einzelne Feld kennen muss.

    Vergleichbar mit einem Mapper/Assembler in einer Java-Anwendung.
    """

    return WorkoutResponse(
        id=workout.id,
        person_id=workout.person_id,
        started_at=workout.started_at,
        status=workout.status.value,
        total_duration_minutes=workout.total_duration_minutes,
        elapsed_seconds=workout.elapsed_seconds,
        distance_m=workout.distance_m,
        video_id=workout.video_id,
        video_position_seconds=workout.video_position_seconds,
        completed_at=workout.completed_at,
        phases=[
            WorkoutPhaseResponse(
                phase_type=phase.phase_type.value,
                duration_minutes=phase.duration_minutes,
                target_heart_rate_min=phase.target_heart_rate_min,
                target_heart_rate_max=phase.target_heart_rate_max,
            )
            for phase in workout.phases
        ],
    )


def to_workout_summary_response(
    summary: WorkoutSummary,
) -> WorkoutSummaryResponse:
    return WorkoutSummaryResponse(
        planned_seconds=summary.planned_seconds,
        elapsed_seconds=summary.elapsed_seconds,
        distance_m=summary.distance_m,
        completion_percent=summary.completion_percent,
        status=summary.status.value,
        heart_rate_summary=(
            WorkoutHeartRateSummaryResponse(
                sample_count=summary.heart_rate_summary.sample_count,
                average_bpm=summary.heart_rate_summary.average_bpm,
                max_bpm=summary.heart_rate_summary.max_bpm,
                below_target_percent=summary.heart_rate_summary.below_target_percent,
                in_target_percent=summary.heart_rate_summary.in_target_percent,
                above_target_percent=summary.heart_rate_summary.above_target_percent,
            )
            if summary.heart_rate_summary is not None
            else None
        ),
        adaptive_evaluation=(
            AdaptiveEvaluationResponse(**vars(summary.adaptive_evaluation))
            if summary.adaptive_evaluation is not None
            else None
        ),
        bike_summary=(
            WorkoutBikeSummaryResponse(
                power_sample_count=summary.bike_summary.power_sample_count,
                average_power_w=summary.bike_summary.average_power_w,
                cadence_sample_count=summary.bike_summary.cadence_sample_count,
                average_cadence_rpm=summary.bike_summary.average_cadence_rpm,
            )
            if summary.bike_summary is not None
            else None
        ),
    )
