from features.person.domain.profile import TrainingGoal
from features.training.domain.coach_message import CoachMessageContext
from features.training.domain.pre_workout import RecommendationReasonCode
from features.training.domain.recommendation import WorkoutType
from features.training.service.pre_workout_reason_builder import PreWorkoutReasonBuilder
from tests.features.training.service.test_pre_workout_coaching_planner import context


def message_context(
    *,
    coaching_context=None,
    reason_codes: tuple[RecommendationReasonCode, ...],
    workout_type: WorkoutType = WorkoutType.BASE_ENDURANCE,
    total_duration_minutes: int = 30,
) -> CoachMessageContext:
    source = coaching_context or context()
    return CoachMessageContext(
        workout_type=workout_type,
        total_duration_minutes=total_duration_minutes,
        reason_codes=reason_codes,
        training_goal=source.training_goal,
        readiness_max_duration_minutes=source.readiness.max_duration_minutes,
        weight_trend_direction=source.weight_trend.direction,
        weight_trend_kg_per_week=source.weight_trend.weekly_change_kg,
        weight_goal_progress=(
            source.weight_goal_progress
            if source.training_goal is TrainingGoal.WEIGHT_LOSS
            else None
        ),
    )


def test_duration_cap_combines_readiness_causes_into_one_sentence() -> None:
    coaching_context = context(
        available_training_minutes=60,
        max_duration_minutes=30,
    )
    reason_codes = (
        RecommendationReasonCode.SHORT_SLEEP,
        RecommendationReasonCode.HIGH_DAILY_ACTIVITY,
        RecommendationReasonCode.HIGH_RECENT_TRAINING_LOAD,
        RecommendationReasonCode.DURATION_REDUCED_FOR_READINESS,
    )

    text = PreWorkoutReasonBuilder().generate(
        context=message_context(
            coaching_context=coaching_context,
            reason_codes=reason_codes,
        ),
    )

    assert "maximal 30 Minuten" in text
    assert "kurzem Schlaf" in text
    assert "hoher Alltagsaktivität" in text
    assert "Belastung der letzten Tage" in text
    assert text.count("30 Minuten") == 1


def test_weight_progress_is_compact_and_does_not_repeat_remaining_distance() -> None:
    coaching_context = context(
        start_weight_kg=100.0,
        current_weight_kg=92.0,
        target_weight_kg=80.0,
    )
    reason_codes = (
        RecommendationReasonCode.READINESS_GOOD,
        RecommendationReasonCode.WEIGHT_LOSS_GOAL,
        RecommendationReasonCode.WEIGHT_TREND_DOWN,
        RecommendationReasonCode.WEIGHT_GOAL_ABOVE_TARGET,
    )

    text = PreWorkoutReasonBuilder().generate(
        context=message_context(
            coaching_context=coaching_context,
            reason_codes=reason_codes,
        ),
    )

    assert "8.0 kg verloren" in text
    assert "40 %" in text
    assert "12.0 kg" not in text


def test_non_capped_short_sleep_gets_one_short_readiness_sentence() -> None:
    coaching_context = context(max_duration_minutes=None)
    reason_codes = (RecommendationReasonCode.SHORT_SLEEP,)

    text = PreWorkoutReasonBuilder().generate(
        context=message_context(
            coaching_context=coaching_context,
            reason_codes=reason_codes,
        ),
    )

    assert "Schlaf war kurz" in text
    assert "maximal" not in text


def test_non_weight_loss_context_does_not_expose_weight_progress() -> None:
    coaching_context = context(training_goal=TrainingGoal.ENDURANCE)
    coach_context = message_context(
        coaching_context=coaching_context,
        reason_codes=(RecommendationReasonCode.READINESS_GOOD,),
    )

    assert coach_context.training_goal is TrainingGoal.ENDURANCE
    assert coach_context.weight_goal_progress is None
