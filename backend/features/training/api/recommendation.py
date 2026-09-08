from datetime import UTC, datetime

from fastapi import HTTPException

from apps.api import wiring
from features.training.domain.heart_rate import get_max_heart_rate
from features.training.domain.recommendation import TrainingRecommendation


def create_training_recommendation(
    person_id: int,
) -> TrainingRecommendation:
    profile = wiring.person_profile_service.get_profile(person_id)

    if profile is None:
        raise HTTPException(
            status_code=404,
            detail="Person profile not found",
        )

    check_in = wiring.check_in_service.get_latest(person_id)

    if check_in is None:
        raise HTTPException(
            status_code=409,
            detail="No check-in available",
        )

    max_heart_rate = get_max_heart_rate(
        profile,
        datetime.now(UTC).date(),
    )

    return wiring.training_recommendation_engine.recommend(
        check_in=check_in,
        max_heart_rate=max_heart_rate,
    )
