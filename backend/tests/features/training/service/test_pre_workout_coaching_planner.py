from datetime import UTC, datetime

from features.check_in.domain.check_in import CheckIn
from features.person.domain.profile import TrainingGoal
from features.training.domain.pre_workout import (
    PreWorkoutCoachingContext,
    RecommendationReasonCode,
)
from features.training.domain.recommendation import WorkoutType
from features.training.domain.recommendation_engine import TrainingRecommendationEngine
from features.training.domain.weight_trend import WeightTrend, WeightTrendDirection
from features.training.service.pre_workout_coaching_planner import PreWorkoutCoachingPlanner


def context(
    *,
    training_goal: TrainingGoal = TrainingGoal.WEIGHT_LOSS,
    energy: int = 4,
    recovery: int = 4,
    muscle_soreness: int = 1,
    stress: int = 2,
    sleep_hours: float | None = 7.5,
    trend_direction: WeightTrendDirection = WeightTrendDirection.DOWN,
) -> PreWorkoutCoachingContext:
    return PreWorkoutCoachingContext(
        check_in=CheckIn(
            person_id=1,
            timestamp=datetime(2026, 9, 14, 8, 0, tzinfo=UTC),
            energy=energy,
            recovery=recovery,
            muscle_soreness=muscle_soreness,
            stress=stress,
            available_training_minutes=30,
            sleep_hours=sleep_hours,
        ),
        max_heart_rate=180,
        training_goal=training_goal,
        weight_trend=WeightTrend(
            direction=trend_direction,
            weekly_change_kg=-0.4 if trend_direction is WeightTrendDirection.DOWN else 0.0,
            sample_count=5,
            span_days=28.0,
        ),
    )


def planner() -> PreWorkoutCoachingPlanner:
    return PreWorkoutCoachingPlanner(TrainingRecommendationEngine())


def test_good_readiness_keeps_base_endurance_and_adds_weight_context() -> None:
    recommendation = planner().recommend(context())

    assert recommendation.workout_type is WorkoutType.BASE_ENDURANCE
    assert RecommendationReasonCode.READINESS_GOOD in recommendation.reason_codes
    assert RecommendationReasonCode.WEIGHT_LOSS_GOAL in recommendation.reason_codes
    assert RecommendationReasonCode.WEIGHT_TREND_DOWN in recommendation.reason_codes
    assert "Gewichtstrend" in recommendation.reason


def test_recovery_has_priority_over_weight_loss_goal() -> None:
    recommendation = planner().recommend(
        context(
            energy=2,
            trend_direction=WeightTrendDirection.UP,
        )
    )

    assert recommendation.workout_type is WorkoutType.RECOVERY
    assert RecommendationReasonCode.LOW_ENERGY in recommendation.reason_codes
    assert RecommendationReasonCode.WEIGHT_TREND_UP in recommendation.reason_codes
    assert "erhöhen die heutige Belastung deshalb aber nicht automatisch" in recommendation.reason


def test_short_sleep_is_explained_without_alone_forcing_recovery() -> None:
    recommendation = planner().recommend(context(sleep_hours=5.5))

    assert recommendation.workout_type is WorkoutType.BASE_ENDURANCE
    assert RecommendationReasonCode.SHORT_SLEEP in recommendation.reason_codes
    assert "Schlaf war kurz" in recommendation.reason


def test_non_weight_loss_goal_does_not_add_weight_reason_codes() -> None:
    recommendation = planner().recommend(context(training_goal=TrainingGoal.ENDURANCE))

    assert RecommendationReasonCode.WEIGHT_LOSS_GOAL not in recommendation.reason_codes
    assert RecommendationReasonCode.WEIGHT_TREND_DOWN not in recommendation.reason_codes
