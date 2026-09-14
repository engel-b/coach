from datetime import UTC, datetime

from features.check_in.domain.check_in import CheckIn
from features.person.domain.profile import TrainingGoal
from features.training.domain.pre_workout import (
    PreWorkoutCoachingContext,
    RecommendationReasonCode,
)
from features.training.domain.readiness import (
    DailyActivityStatus,
    ReadinessContext,
    RecentTrainingLoadStatus,
    SleepStatus,
)
from features.training.domain.recommendation import WorkoutType
from features.training.domain.recommendation_engine import TrainingRecommendationEngine
from features.training.domain.weight_goal_progress import (
    WeightGoalProgress,
    WeightGoalStatus,
)
from features.training.domain.weight_trend import WeightTrend, WeightTrendDirection
from features.training.service.pre_workout_coaching_planner import PreWorkoutCoachingPlanner


def context(
    *,
    training_goal: TrainingGoal = TrainingGoal.WEIGHT_LOSS,
    energy: int = 4,
    recovery: int = 4,
    muscle_soreness: int = 1,
    stress: int = 2,
    available_training_minutes: int = 30,
    sleep_status: SleepStatus = SleepStatus.ADEQUATE,
    daily_activity_status: DailyActivityStatus = DailyActivityStatus.NORMAL,
    recent_training_load_status: RecentTrainingLoadStatus = RecentTrainingLoadStatus.LOW,
    max_duration_minutes: int | None = None,
    trend_direction: WeightTrendDirection = WeightTrendDirection.DOWN,
    start_weight_kg: float | None = 100.0,
    current_weight_kg: float | None = 92.4,
    target_weight_kg: float | None = 82.0,
) -> PreWorkoutCoachingContext:
    return PreWorkoutCoachingContext(
        check_in=CheckIn(
            person_id=1,
            timestamp=datetime(2026, 9, 14, 8, 0, tzinfo=UTC),
            energy=energy,
            recovery=recovery,
            muscle_soreness=muscle_soreness,
            stress=stress,
            available_training_minutes=available_training_minutes,
            current_weight_kg=current_weight_kg,
        ),
        max_heart_rate=180,
        training_goal=training_goal,
        weight_trend=WeightTrend(
            direction=trend_direction,
            weekly_change_kg=-0.4 if trend_direction is WeightTrendDirection.DOWN else 0.0,
            sample_count=5,
            span_days=28.0,
        ),
        weight_goal_progress=WeightGoalProgress(
            status=(
                WeightGoalStatus.NO_GOAL
                if target_weight_kg is None
                else WeightGoalStatus.NO_CURRENT_WEIGHT
                if current_weight_kg is None
                else WeightGoalStatus.ABOVE_TARGET
                if current_weight_kg > target_weight_kg
                else WeightGoalStatus.BELOW_TARGET
                if current_weight_kg < target_weight_kg
                else WeightGoalStatus.AT_TARGET
            ),
            start_weight_kg=start_weight_kg,
            current_weight_kg=current_weight_kg,
            target_weight_kg=target_weight_kg,
            remaining_kg=(
                None
                if current_weight_kg is None or target_weight_kg is None
                else round(current_weight_kg - target_weight_kg, 1)
            ),
            lost_since_start_kg=(
                None
                if start_weight_kg is None
                or current_weight_kg is None
                or target_weight_kg is None
                or start_weight_kg <= target_weight_kg
                else round(start_weight_kg - current_weight_kg, 1)
            ),
            progress_percent=(
                None
                if start_weight_kg is None
                or current_weight_kg is None
                or target_weight_kg is None
                or start_weight_kg <= target_weight_kg
                else round(
                    min(
                        100.0,
                        max(
                            0.0,
                            (start_weight_kg - current_weight_kg)
                            / (start_weight_kg - target_weight_kg)
                            * 100.0,
                        ),
                    ),
                    1,
                )
            ),
        ),
        readiness=ReadinessContext(
            sleep_status=sleep_status,
            daily_activity_status=daily_activity_status,
            recent_training_load_status=recent_training_load_status,
            recent_training_minutes=0.0,
            recent_workout_count=0,
            max_duration_minutes=max_duration_minutes,
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
    assert recommendation.weight_goal_progress is not None
    assert recommendation.weight_goal_progress.progress_percent == 42.2
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


def test_short_sleep_caps_long_session_without_alone_forcing_recovery() -> None:
    recommendation = planner().recommend(
        context(
            available_training_minutes=60,
            sleep_status=SleepStatus.SHORT,
            max_duration_minutes=30,
        )
    )

    assert recommendation.workout_type is WorkoutType.BASE_ENDURANCE
    assert recommendation.total_duration_minutes == 30
    assert RecommendationReasonCode.SHORT_SLEEP in recommendation.reason_codes
    assert RecommendationReasonCode.DURATION_REDUCED_FOR_READINESS in recommendation.reason_codes
    assert "Schlaf war kurz" in recommendation.reason


def test_high_recent_training_load_is_visible_and_caps_duration() -> None:
    recommendation = planner().recommend(
        context(
            available_training_minutes=60,
            recent_training_load_status=RecentTrainingLoadStatus.HIGH,
            max_duration_minutes=30,
        )
    )

    assert recommendation.total_duration_minutes == 30
    assert RecommendationReasonCode.HIGH_RECENT_TRAINING_LOAD in recommendation.reason_codes
    assert RecommendationReasonCode.DURATION_REDUCED_FOR_READINESS in recommendation.reason_codes


def test_high_daily_activity_is_visible_and_caps_duration() -> None:
    recommendation = planner().recommend(
        context(
            available_training_minutes=45,
            daily_activity_status=DailyActivityStatus.HIGH,
            max_duration_minutes=30,
        )
    )

    assert recommendation.total_duration_minutes == 30
    assert RecommendationReasonCode.HIGH_DAILY_ACTIVITY in recommendation.reason_codes


def test_non_weight_loss_goal_does_not_add_weight_reason_codes() -> None:
    recommendation = planner().recommend(context(training_goal=TrainingGoal.ENDURANCE))

    assert RecommendationReasonCode.WEIGHT_LOSS_GOAL not in recommendation.reason_codes
    assert RecommendationReasonCode.WEIGHT_TREND_DOWN not in recommendation.reason_codes


def test_weight_goal_distance_is_explained_without_changing_workout_load() -> None:
    recommendation = planner().recommend(
        context(
            current_weight_kg=92.4,
            target_weight_kg=82.0,
        )
    )

    assert recommendation.workout_type is WorkoutType.BASE_ENDURANCE
    assert RecommendationReasonCode.WEIGHT_GOAL_ABOVE_TARGET in recommendation.reason_codes
    assert "10.4 kg" in recommendation.reason


def test_missing_current_weight_is_explicit_for_weight_loss_goal() -> None:
    recommendation = planner().recommend(context(current_weight_kg=None))

    assert RecommendationReasonCode.WEIGHT_GOAL_NO_CURRENT_WEIGHT in recommendation.reason_codes
    assert "fehlt aktuell ein Gewichtswert" in recommendation.reason


def test_weight_goal_progress_since_start_is_explained() -> None:
    recommendation = planner().recommend(
        context(
            start_weight_kg=100.0,
            current_weight_kg=92.0,
            target_weight_kg=80.0,
        )
    )

    assert "8.0 kg verloren" in recommendation.reason
    assert "40 %" in recommendation.reason
