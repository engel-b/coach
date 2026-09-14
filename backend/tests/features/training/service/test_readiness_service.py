from datetime import UTC, datetime, timedelta

from features.check_in.domain.check_in import CheckIn
from features.training.domain.readiness import (
    DailyActivityStatus,
    RecentTrainingLoadStatus,
    RecentTrainingSession,
    SleepStatus,
)
from features.training.service.readiness_service import ReadinessService

NOW = datetime(2026, 9, 14, 8, 0, tzinfo=UTC)


def check_in(*, sleep_hours: float | None = 7.5, steps: int | None = 4_000) -> CheckIn:
    return CheckIn(
        person_id=1,
        timestamp=NOW,
        energy=4,
        recovery=4,
        muscle_soreness=1,
        stress=2,
        available_training_minutes=60,
        sleep_hours=sleep_hours,
        steps=steps,
    )


def session(*, days_ago: float, active_minutes: float) -> RecentTrainingSession:
    return RecentTrainingSession(
        started_at=NOW - timedelta(days=days_ago),
        active_minutes=active_minutes,
    )


def test_good_signals_do_not_cap_duration() -> None:
    readiness = ReadinessService().assess(
        check_in=check_in(),
        recent_sessions=[session(days_ago=1, active_minutes=30)],
    )

    assert readiness.sleep_status is SleepStatus.ADEQUATE
    assert readiness.daily_activity_status is DailyActivityStatus.NORMAL
    assert readiness.recent_training_load_status is RecentTrainingLoadStatus.MODERATE
    assert readiness.max_duration_minutes is None


def test_short_sleep_caps_duration_without_claiming_recovery() -> None:
    readiness = ReadinessService().assess(
        check_in=check_in(sleep_hours=5.5),
        recent_sessions=[],
    )

    assert readiness.sleep_status is SleepStatus.SHORT
    assert readiness.max_duration_minutes == 30


def test_high_daily_activity_caps_duration() -> None:
    readiness = ReadinessService().assess(
        check_in=check_in(steps=12_500),
        recent_sessions=[],
    )

    assert readiness.daily_activity_status is DailyActivityStatus.HIGH
    assert readiness.max_duration_minutes == 30


def test_recent_training_load_uses_only_configured_window() -> None:
    readiness = ReadinessService().assess(
        check_in=check_in(),
        recent_sessions=[
            session(days_ago=1, active_minutes=50),
            session(days_ago=2, active_minutes=45),
            session(days_ago=5, active_minutes=120),
        ],
    )

    assert readiness.recent_training_minutes == 95.0
    assert readiness.recent_workout_count == 2
    assert readiness.recent_training_load_status is RecentTrainingLoadStatus.HIGH
    assert readiness.max_duration_minutes == 30


def test_missing_sleep_and_steps_do_not_create_a_caution_signal() -> None:
    readiness = ReadinessService().assess(
        check_in=check_in(sleep_hours=None, steps=None),
        recent_sessions=[],
    )

    assert readiness.sleep_status is SleepStatus.UNKNOWN
    assert readiness.daily_activity_status is DailyActivityStatus.UNKNOWN
    assert readiness.max_duration_minutes is None
