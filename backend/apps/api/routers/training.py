from typing import Annotated

from fastapi import APIRouter, HTTPException, Path

from apps.api import wiring
from apps.api.recommendation import create_training_recommendation
from contracts.training import (
    TrainingRecommendationResponse,
    WorkoutPhaseResponse,
)

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
