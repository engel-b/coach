from features.training.domain.heart_rate_history import (
    HeartRateHistoryContext,
    HeartRateHistoryStatus,
    HeartRateResponseTrend,
    LoadAdjustedHeartRateTrend,
)
from features.training.domain.load_response import LoadResponseStatus
from features.training.domain.readiness import (
    DailyActivityStatus,
    ReadinessContext,
    RecentTrainingLoadStatus,
    SleepStatus,
)
from features.training.domain.recommendation import WorkoutType
from features.training.service.load_response_service import LoadResponseService


def readiness(*, caution: bool = False) -> ReadinessContext:
    return ReadinessContext(
        sleep_status=SleepStatus.SHORT if caution else SleepStatus.ADEQUATE,
        daily_activity_status=DailyActivityStatus.NORMAL,
        recent_training_load_status=RecentTrainingLoadStatus.LOW,
        recent_training_minutes=0,
        recent_workout_count=0,
        max_duration_minutes=30 if caution else None,
    )


def history(adjusted: LoadAdjustedHeartRateTrend) -> HeartRateHistoryContext:
    return HeartRateHistoryContext(
        status=HeartRateHistoryStatus.MOSTLY_IN_TARGET,
        workout_count=5,
        workout_type=WorkoutType.BASE_ENDURANCE,
        response_trend=HeartRateResponseTrend.LOWER,
        load_adjusted_trend=adjusted,
        median_power_w=120,
        median_cadence_rpm=76.5,
    )


def test_describes_lower_hr_at_similar_load() -> None:
    context = LoadResponseService().assess(
        history=history(LoadAdjustedHeartRateTrend.LOWER_AT_SIMILAR_POWER),
        readiness=readiness(),
        workout_type=WorkoutType.BASE_ENDURANCE,
    )

    assert context.status is LoadResponseStatus.LOWER_HR_AT_SIMILAR_LOAD
    assert context.median_power_w == 120
    assert context.median_cadence_rpm == 76.5
    assert context.readiness_caution is False


def test_keeps_readiness_as_separate_caution_signal() -> None:
    context = LoadResponseService().assess(
        history=history(LoadAdjustedHeartRateTrend.STABLE_AT_SIMILAR_POWER),
        readiness=readiness(caution=True),
        workout_type=WorkoutType.BASE_ENDURANCE,
    )

    assert context.status is LoadResponseStatus.STABLE
    assert context.readiness_caution is True


def test_insufficient_power_history_stays_insufficient() -> None:
    context = LoadResponseService().assess(
        history=history(LoadAdjustedHeartRateTrend.INSUFFICIENT_DATA),
        readiness=readiness(),
        workout_type=WorkoutType.BASE_ENDURANCE,
    )

    assert context.status is LoadResponseStatus.INSUFFICIENT_DATA
