from datetime import UTC, datetime, timedelta

import pytest

from features.coaching.domain.live_coaching import (
    CoachingAction,
    LiveCoachingRules,
)
from features.coaching.service.live_coaching_coordinator import (
    LiveCoachingCoordinator,
)
from features.coaching.service.live_coaching_engine import LiveCoachingEngine
from features.telemetry.domain.health.heart_rate import HeartRateSample
from features.training.domain.recommendation import (
    WorkoutPhase,
    WorkoutPhaseType,
)
from features.workout.domain.session import WorkoutSession, WorkoutStatus


def create_workout(
    *,
    workout_id: str = "workout-1",
) -> WorkoutSession:
    return WorkoutSession(
        id=workout_id,
        person_id=1,
        started_at=datetime.now(UTC),
        status=WorkoutStatus.RUNNING,
        total_duration_minutes=30,
        phases=(
            WorkoutPhase(
                phase_type=WorkoutPhaseType.WARM_UP,
                duration_minutes=5,
                target_heart_rate_min=100,
                target_heart_rate_max=120,
            ),
            WorkoutPhase(
                phase_type=WorkoutPhaseType.MAIN,
                duration_minutes=20,
                target_heart_rate_min=125,
                target_heart_rate_max=145,
            ),
            WorkoutPhase(
                phase_type=WorkoutPhaseType.COOL_DOWN,
                duration_minutes=5,
                target_heart_rate_min=95,
                target_heart_rate_max=115,
            ),
        ),
    )


def create_coordinator() -> LiveCoachingCoordinator:
    return LiveCoachingCoordinator(
        coaching_engine=LiveCoachingEngine(
            rules=LiveCoachingRules(
                deviation_seconds_before_action=20.0,
            )
        )
    )


def test_coordinator_has_no_active_workout_initially() -> None:
    coordinator = create_coordinator()

    assert coordinator.active_workout_id is None


def test_start_creates_active_coaching_session() -> None:
    coordinator = create_coordinator()

    coordinator.start(create_workout())

    assert coordinator.active_workout_id == "workout-1"


def test_second_active_workout_is_rejected() -> None:
    coordinator = create_coordinator()

    coordinator.start(create_workout())

    with pytest.raises(
        RuntimeError,
        match="a live coaching session is already active",
    ):
        coordinator.start(
            create_workout(
                workout_id="workout-2",
            )
        )


def test_heart_rate_without_active_workout_is_ignored() -> None:
    coordinator = create_coordinator()

    decision = coordinator.handle_heart_rate(
        HeartRateSample(
            device_id="heart-rate-1",
            timestamp=datetime.now(UTC),
            bpm=150,
        )
    )

    assert decision is None


def test_checkpoint_changes_current_phase() -> None:
    coordinator = create_coordinator()
    coordinator.start(create_workout())

    coordinator.update_elapsed_seconds(
        workout_id="workout-1",
        elapsed_seconds=300,
    )

    decision = coordinator.handle_heart_rate(
        HeartRateSample(
            device_id="heart-rate-1",
            timestamp=datetime.now(UTC),
            bpm=135,
        )
    )

    assert decision is not None
    assert decision.target_min_bpm == 125
    assert decision.target_max_bpm == 145


def test_sustained_high_heart_rate_produces_coaching_decision() -> None:
    coordinator = create_coordinator()
    coordinator.start(create_workout())

    coordinator.update_elapsed_seconds(
        workout_id="workout-1",
        elapsed_seconds=300,
    )

    start = datetime.now(UTC)

    first = coordinator.handle_heart_rate(
        HeartRateSample(
            device_id="heart-rate-1",
            timestamp=start,
            bpm=150,
        )
    )

    second = coordinator.handle_heart_rate(
        HeartRateSample(
            device_id="heart-rate-1",
            timestamp=start + timedelta(seconds=21),
            bpm=149,
        )
    )

    assert first is not None
    assert second is not None

    assert first.action is CoachingAction.NONE
    assert second.action is CoachingAction.REDUCE_INTENSITY


def test_finish_removes_active_session() -> None:
    coordinator = create_coordinator()
    coordinator.start(create_workout())

    coordinator.finish(
        workout_id="workout-1",
    )

    assert coordinator.active_workout_id is None


def test_wrong_workout_cannot_update_active_session() -> None:
    coordinator = create_coordinator()
    coordinator.start(create_workout())

    with pytest.raises(
        ValueError,
        match="is not the active coaching workout",
    ):
        coordinator.update_elapsed_seconds(
            workout_id="workout-2",
            elapsed_seconds=100,
        )
