from features.training.domain.adaptive_workout import (
    AdaptiveWorkoutAction,
    AdaptiveWorkoutReasonCode,
)
from features.training.domain.heart_rate_history import (
    HeartRateHistoryContext,
    HeartRateHistoryStatus,
    HeartRateResponseTrend,
    LoadAdjustedHeartRateTrend,
)
from features.training.domain.load_response import LoadResponseContext, LoadResponseStatus
from features.training.domain.readiness import (
    DailyActivityStatus,
    ReadinessContext,
    RecentTrainingLoadStatus,
    SleepStatus,
)
from features.training.domain.recommendation import WorkoutType
from features.training.service.adaptive_workout_policy import AdaptiveWorkoutPolicy


def readiness(*, duration_cap: int | None = None) -> ReadinessContext:
    return ReadinessContext(
        sleep_status=SleepStatus.SHORT if duration_cap is not None else SleepStatus.ADEQUATE,
        daily_activity_status=DailyActivityStatus.NORMAL,
        recent_training_load_status=RecentTrainingLoadStatus.LOW,
        recent_training_minutes=0.0,
        recent_workout_count=0,
        max_duration_minutes=duration_cap,
    )


def history(
    *,
    status: HeartRateHistoryStatus = HeartRateHistoryStatus.MOSTLY_IN_TARGET,
    duration_cap: int | None = None,
) -> HeartRateHistoryContext:
    return HeartRateHistoryContext(
        status=status,
        workout_count=5,
        workout_type=WorkoutType.BASE_ENDURANCE,
        max_duration_minutes=duration_cap,
        response_trend=HeartRateResponseTrend.HIGHER,
        load_adjusted_trend=LoadAdjustedHeartRateTrend.HIGHER_AT_SIMILAR_POWER,
    )


def load_response(status: LoadResponseStatus) -> LoadResponseContext:
    return LoadResponseContext(
        status=status,
        workout_type=WorkoutType.BASE_ENDURANCE,
        comparable_workout_count=5,
        heart_rate_trend=HeartRateResponseTrend.HIGHER,
        load_adjusted_heart_rate_trend=(
            LoadAdjustedHeartRateTrend.HIGHER_AT_SIMILAR_POWER
            if status is LoadResponseStatus.HIGHER_HR_AT_SIMILAR_LOAD
            else LoadAdjustedHeartRateTrend.STABLE_AT_SIMILAR_POWER
        ),
        median_power_w=120,
        median_cadence_rpm=76.0,
        readiness_caution=False,
    )


def test_recovery_plan_is_reported_as_already_reflected() -> None:
    advice = AdaptiveWorkoutPolicy().assess(
        workout_type=WorkoutType.RECOVERY,
        available_training_minutes=30,
        readiness=readiness(),
        heart_rate_history=history(),
        load_response=load_response(LoadResponseStatus.STABLE),
    )

    assert advice.action is AdaptiveWorkoutAction.PREFER_RECOVERY
    assert advice.plan_reflects_advice is True
    assert advice.reason_codes == (AdaptiveWorkoutReasonCode.RECOVERY_PLAN_SELECTED,)


def test_existing_readiness_cap_is_exposed_as_applied_duration_reduction() -> None:
    advice = AdaptiveWorkoutPolicy().assess(
        workout_type=WorkoutType.BASE_ENDURANCE,
        available_training_minutes=60,
        readiness=readiness(duration_cap=30),
        heart_rate_history=history(),
        load_response=load_response(LoadResponseStatus.STABLE),
    )

    assert advice.action is AdaptiveWorkoutAction.REDUCE_DURATION
    assert advice.plan_reflects_advice is True
    assert advice.recommended_duration_minutes == 30
    assert AdaptiveWorkoutReasonCode.READINESS_DURATION_CAP in advice.reason_codes


def test_strong_high_hr_history_extends_warmup_without_changing_intensity() -> None:
    advice = AdaptiveWorkoutPolicy().assess(
        workout_type=WorkoutType.BASE_ENDURANCE,
        available_training_minutes=30,
        readiness=readiness(),
        heart_rate_history=history(status=HeartRateHistoryStatus.MOSTLY_ABOVE_TARGET),
        load_response=load_response(LoadResponseStatus.HIGHER_HR_AT_SIMILAR_LOAD),
    )

    assert advice.action is AdaptiveWorkoutAction.EXTEND_WARMUP
    assert advice.plan_reflects_advice is True
    assert advice.recommended_duration_minutes is None


def test_higher_hr_at_similar_load_suggests_longer_warmup_when_history_is_not_dominantly_high() -> (
    None
):
    advice = AdaptiveWorkoutPolicy().assess(
        workout_type=WorkoutType.BASE_ENDURANCE,
        available_training_minutes=30,
        readiness=readiness(),
        heart_rate_history=history(),
        load_response=load_response(LoadResponseStatus.HIGHER_HR_AT_SIMILAR_LOAD),
    )

    assert advice.action is AdaptiveWorkoutAction.EXTEND_WARMUP
    assert advice.plan_reflects_advice is True


def test_lower_hr_at_similar_load_never_triggers_automatic_progression() -> None:
    advice = AdaptiveWorkoutPolicy().assess(
        workout_type=WorkoutType.BASE_ENDURANCE,
        available_training_minutes=30,
        readiness=readiness(),
        heart_rate_history=history(),
        load_response=load_response(LoadResponseStatus.LOWER_HR_AT_SIMILAR_LOAD),
    )

    assert advice.action is AdaptiveWorkoutAction.KEEP_PLAN
    assert advice.plan_reflects_advice is True
    assert AdaptiveWorkoutReasonCode.NO_AUTOMATIC_PROGRESSION in advice.reason_codes


def test_advice_carries_the_deterministic_decision_context() -> None:
    advice = AdaptiveWorkoutPolicy().assess(
        workout_type=WorkoutType.BASE_ENDURANCE,
        available_training_minutes=60,
        readiness=readiness(duration_cap=30),
        heart_rate_history=history(status=HeartRateHistoryStatus.MOSTLY_ABOVE_TARGET),
        load_response=load_response(LoadResponseStatus.HIGHER_HR_AT_SIMILAR_LOAD),
    )

    context = advice.decision_context
    assert context.workout_type is WorkoutType.BASE_ENDURANCE
    assert context.available_training_minutes == 60
    assert context.readiness_max_duration_minutes == 30
    assert context.heart_rate_history_status is HeartRateHistoryStatus.MOSTLY_ABOVE_TARGET
    assert context.load_response_status is LoadResponseStatus.HIGHER_HR_AT_SIMILAR_LOAD
    assert context.comparable_workout_count == 5
