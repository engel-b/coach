from typing import Annotated

from fastapi import APIRouter, HTTPException, Path

from apps.api import wiring
from features.training.api.contracts.training import (
    HeartRateHistoryResponse,
    HeartRateTargetBasisResponse,
    LoadResponseResponse,
    TrainingRecommendationResponse,
    WeightGoalProgressResponse,
    WorkoutPhaseResponse,
)
from features.training.api.recommendation import create_training_recommendation

router = APIRouter(tags=["Training"])


PersonId = Annotated[
    int,
    Path(
        title="Personen-ID",
        description="Stabile numerische ID der Person.",
    ),
]


@router.get(
    "/api/persons/{person_id}/training-recommendation",
    response_model=TrainingRecommendationResponse,
    response_model_by_alias=True,
    summary="Trainingsempfehlung erstellen",
    description=(
        "Erstellt eine individuelle Trainingsempfehlung auf Basis "
        "des Personenprofils und des letzten Check-ins. Die Empfehlung "
        "enthält den Trainingstyp, die Gesamtdauer, eine Begründung "
        "und die einzelnen Trainingsphasen mit Zielpulsbereichen.\n\n"
        "Es wird kein Workout gestartet oder gespeichert. Dafür steht "
        "der separate Start-Endpunkt zur Verfügung."
    ),
    responses={
        404: {
            "description": (
                "Die Person oder das erforderliche Personenprofil wurde nicht gefunden."
            ),
        },
        409: {
            "description": (
                "Für die Person liegt noch kein Check-in vor. "
                "Vor der Empfehlung muss zunächst ein Check-in "
                "erfasst werden."
            ),
        },
    },
)
async def training_recommendation(
    person_id: int,
) -> TrainingRecommendationResponse:
    person = wiring.person_service.get_person(person_id)

    if person is None:
        raise HTTPException(
            status_code=404,
            detail="Person not found",
        )

    recommendation = create_training_recommendation(person_id)

    if recommendation.heart_rate_target_basis is None:
        raise RuntimeError("training recommendation is missing heart-rate target basis")

    return TrainingRecommendationResponse(
        workout_type=recommendation.workout_type.value,
        total_duration_minutes=(recommendation.total_duration_minutes),
        reason=recommendation.reason,
        heart_rate_target_basis=HeartRateTargetBasisResponse(
            method=recommendation.heart_rate_target_basis.method.value,
            max_heart_rate_bpm=recommendation.heart_rate_target_basis.max_heart_rate_bpm,
            resting_heart_rate_bpm=(recommendation.heart_rate_target_basis.resting_heart_rate_bpm),
            reference_resting_heart_rate_bpm=(
                recommendation.heart_rate_target_basis.reference_resting_heart_rate_bpm
            ),
            resting_heart_rate_source=(
                recommendation.heart_rate_target_basis.resting_heart_rate_source.value
                if recommendation.heart_rate_target_basis.resting_heart_rate_source is not None
                else None
            ),
            resting_heart_rate_sample_count=(
                recommendation.heart_rate_target_basis.resting_heart_rate_sample_count
            ),
        ),
        heart_rate_history=(
            None
            if recommendation.heart_rate_history is None
            else HeartRateHistoryResponse(
                status=recommendation.heart_rate_history.status.value,
                workout_count=recommendation.heart_rate_history.workout_count,
                workout_type=(
                    recommendation.heart_rate_history.workout_type.value
                    if recommendation.heart_rate_history.workout_type is not None
                    else None
                ),
                median_in_target_percent=(
                    recommendation.heart_rate_history.median_in_target_percent
                ),
                median_above_target_percent=(
                    recommendation.heart_rate_history.median_above_target_percent
                ),
                median_below_target_percent=(
                    recommendation.heart_rate_history.median_below_target_percent
                ),
                max_duration_minutes=(recommendation.heart_rate_history.max_duration_minutes),
                response_trend=(recommendation.heart_rate_history.response_trend.value),
                median_target_position_percent=(
                    recommendation.heart_rate_history.median_target_position_percent
                ),
                target_position_change_points=(
                    recommendation.heart_rate_history.target_position_change_points
                ),
                load_adjusted_trend=(recommendation.heart_rate_history.load_adjusted_trend.value),
                median_power_w=recommendation.heart_rate_history.median_power_w,
                median_cadence_rpm=recommendation.heart_rate_history.median_cadence_rpm,
                power_change_percent=(recommendation.heart_rate_history.power_change_percent),
            )
        ),
        load_response=(
            None
            if recommendation.load_response is None
            else LoadResponseResponse(
                status=recommendation.load_response.status.value,
                workout_type=recommendation.load_response.workout_type.value,
                comparable_workout_count=(recommendation.load_response.comparable_workout_count),
                heart_rate_trend=recommendation.load_response.heart_rate_trend.value,
                load_adjusted_heart_rate_trend=(
                    recommendation.load_response.load_adjusted_heart_rate_trend.value
                ),
                median_power_w=recommendation.load_response.median_power_w,
                median_cadence_rpm=recommendation.load_response.median_cadence_rpm,
                readiness_caution=recommendation.load_response.readiness_caution,
            )
        ),
        weight_goal_progress=(
            None
            if recommendation.weight_goal_progress is None
            else WeightGoalProgressResponse(
                status=recommendation.weight_goal_progress.status.value,
                start_weight_kg=recommendation.weight_goal_progress.start_weight_kg,
                current_weight_kg=recommendation.weight_goal_progress.current_weight_kg,
                target_weight_kg=recommendation.weight_goal_progress.target_weight_kg,
                remaining_kg=recommendation.weight_goal_progress.remaining_kg,
                lost_since_start_kg=recommendation.weight_goal_progress.lost_since_start_kg,
                progress_percent=recommendation.weight_goal_progress.progress_percent,
            )
        ),
        reason_codes=[reason.value for reason in recommendation.reason_codes],
        phases=[
            WorkoutPhaseResponse(
                phase_type=phase.phase_type.value,
                duration_minutes=phase.duration_minutes,
                target_heart_rate_min=(phase.target_heart_rate_min),
                target_heart_rate_max=(phase.target_heart_rate_max),
            )
            for phase in recommendation.phases
        ],
    )
