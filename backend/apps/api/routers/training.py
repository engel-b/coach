from fastapi import APIRouter, HTTPException

from apps.api import wiring
from apps.api.recommendation import create_training_recommendation
from contracts.training import (
    TrainingRecommendationResponse,
    WorkoutPhaseResponse,
)

router = APIRouter()


@router.get(
    "/api/persons/{person_id}/training-recommendation",
    response_model=TrainingRecommendationResponse,
    response_model_by_alias=True,
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

    return TrainingRecommendationResponse(
        workout_type=recommendation.workout_type.value,
        total_duration_minutes=(recommendation.total_duration_minutes),
        reason=recommendation.reason,
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
