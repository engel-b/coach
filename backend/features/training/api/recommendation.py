from datetime import UTC, datetime

from fastapi import HTTPException

from apps.api import wiring
from features.training.domain.heart_rate import get_max_heart_rate
from features.training.domain.pre_workout import PreWorkoutCoachingContext
from features.training.domain.readiness import RecentTrainingSession
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

    history = wiring.check_in_service.get_history(person_id, limit=90)
    weight_trend = wiring.weight_trend_service.calculate(
        check_ins=history,
        as_of=check_in.timestamp,
    )

    weight_goal_progress = wiring.weight_goal_progress_service.calculate(
        start_weight_kg=profile.start_weight_kg,
        current_weight_kg=check_in.current_weight_kg,
        target_weight_kg=profile.target_weight_kg,
    )

    recent_workouts = wiring.workout_service.get_for_person(person_id, limit=20)
    readiness = wiring.readiness_service.assess(
        check_in=check_in,
        recent_sessions=[
            RecentTrainingSession(
                started_at=workout.started_at,
                active_minutes=workout.elapsed_seconds / 60.0,
            )
            for workout in recent_workouts
        ],
    )

    return wiring.pre_workout_coaching_planner.recommend(
        PreWorkoutCoachingContext(
            check_in=check_in,
            max_heart_rate=max_heart_rate,
            resting_heart_rate=profile.resting_heart_rate_bpm,
            training_goal=profile.training_goal,
            weight_trend=weight_trend,
            weight_goal_progress=weight_goal_progress,
            readiness=readiness,
        )
    )
