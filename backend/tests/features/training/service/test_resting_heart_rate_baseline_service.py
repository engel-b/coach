from datetime import UTC, datetime, timedelta

from features.check_in.domain.check_in import CheckIn
from features.training.domain.heart_rate_target import HeartRateTargetSource
from features.training.service.resting_heart_rate_baseline_service import (
    RestingHeartRateBaselineService,
)


def _check_in(*, timestamp: datetime, resting_heart_rate_bpm: int | None) -> CheckIn:
    return CheckIn(
        person_id=1,
        timestamp=timestamp,
        energy=4,
        recovery=4,
        muscle_soreness=1,
        stress=2,
        available_training_minutes=30,
        resting_heart_rate_bpm=resting_heart_rate_bpm,
    )


def test_uses_median_of_recent_check_in_measurements() -> None:
    now = datetime(2026, 9, 23, tzinfo=UTC)
    baseline = RestingHeartRateBaselineService().calculate(
        check_ins=[
            _check_in(timestamp=now, resting_heart_rate_bpm=96),
            _check_in(timestamp=now - timedelta(days=1), resting_heart_rate_bpm=78),
            _check_in(timestamp=now - timedelta(days=2), resting_heart_rate_bpm=80),
            _check_in(timestamp=now - timedelta(days=3), resting_heart_rate_bpm=79),
        ],
        as_of=now,
        profile_resting_heart_rate_bpm=72,
    )

    assert baseline.value_bpm == 80
    assert baseline.source is HeartRateTargetSource.CHECK_IN_BASELINE
    assert baseline.sample_count == 4


def test_profile_remains_fallback_until_enough_measurements_exist() -> None:
    now = datetime(2026, 9, 23, tzinfo=UTC)
    baseline = RestingHeartRateBaselineService().calculate(
        check_ins=[
            _check_in(timestamp=now, resting_heart_rate_bpm=80),
            _check_in(timestamp=now - timedelta(days=1), resting_heart_rate_bpm=82),
        ],
        as_of=now,
        profile_resting_heart_rate_bpm=74,
    )

    assert baseline.value_bpm == 74
    assert baseline.source is HeartRateTargetSource.PROFILE
    assert baseline.sample_count == 0


def test_old_measurements_do_not_build_current_baseline() -> None:
    now = datetime(2026, 9, 23, tzinfo=UTC)
    baseline = RestingHeartRateBaselineService().calculate(
        check_ins=[
            _check_in(timestamp=now - timedelta(days=31), resting_heart_rate_bpm=80),
            _check_in(timestamp=now - timedelta(days=32), resting_heart_rate_bpm=81),
            _check_in(timestamp=now - timedelta(days=33), resting_heart_rate_bpm=82),
        ],
        as_of=now,
        profile_resting_heart_rate_bpm=None,
    )

    assert baseline.value_bpm is None
    assert baseline.source is None
