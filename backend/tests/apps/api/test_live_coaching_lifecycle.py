from datetime import UTC, datetime, timedelta

from apps.api.live_coaching_lifecycle import LiveCoachingLifecycle
from features.coaching.domain.live_coaching import CoachingAction, LiveCoachingRules
from features.coaching.service.live_coaching_coordinator import LiveCoachingCoordinator
from features.coaching.service.live_coaching_engine import LiveCoachingEngine
from features.telemetry.domain.health.heart_rate import HeartRateSample
from features.training.domain.recommendation import WorkoutPhase, WorkoutPhaseType
from features.workout.domain.session import WorkoutSession, WorkoutStatus


def create_workout(
    *,
    workout_id: str = "workout-1",
    elapsed_seconds: int = 0,
    status: WorkoutStatus = WorkoutStatus.RUNNING,
) -> WorkoutSession:
    return WorkoutSession(
        id=workout_id,
        person_id=1,
        started_at=datetime.now(UTC),
        status=status,
        total_duration_minutes=30,
        elapsed_seconds=elapsed_seconds,
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


def create_lifecycle() -> LiveCoachingLifecycle:
    coordinator = LiveCoachingCoordinator(
        coaching_engine=LiveCoachingEngine(
            rules=LiveCoachingRules(
                deviation_seconds_before_action=20.0,
            )
        )
    )

    return LiveCoachingLifecycle(
        coordinator=coordinator,
    )


def test_started_workout_becomes_active() -> None:
    lifecycle = create_lifecycle()

    lifecycle.workout_started(create_workout())

    assert lifecycle.active_workout_id == "workout-1"


def test_new_workout_replaces_previous_coaching_focus() -> None:
    lifecycle = create_lifecycle()

    lifecycle.workout_started(create_workout(workout_id="workout-1"))
    lifecycle.workout_started(create_workout(workout_id="workout-2"))

    assert lifecycle.active_workout_id == "workout-2"


def test_checkpoint_updates_phase_used_for_heart_rate_evaluation() -> None:
    lifecycle = create_lifecycle()

    lifecycle.workout_started(create_workout())
    lifecycle.workout_checkpointed(
        create_workout(
            elapsed_seconds=300,
        )
    )

    lifecycle.handle_heart_rate(
        HeartRateSample(
            device_id="heart-rate-1",
            timestamp=datetime.now(UTC),
            bpm=135,
        )
    )

    assert lifecycle.last_decision is not None
    assert lifecycle.last_decision.target_min_bpm == 125
    assert lifecycle.last_decision.target_max_bpm == 145


def test_heart_rate_is_evaluated_for_active_workout() -> None:
    lifecycle = create_lifecycle()
    lifecycle.workout_started(
        create_workout(
            elapsed_seconds=300,
        )
    )

    start = datetime.now(UTC)

    lifecycle.handle_heart_rate(
        HeartRateSample(
            device_id="heart-rate-1",
            timestamp=start,
            bpm=150,
        )
    )
    lifecycle.handle_heart_rate(
        HeartRateSample(
            device_id="heart-rate-1",
            timestamp=start + timedelta(seconds=21),
            bpm=149,
        )
    )

    assert lifecycle.last_decision is not None
    assert lifecycle.last_decision.action is CoachingAction.REDUCE_INTENSITY


def test_finished_workout_removes_coaching_session() -> None:
    lifecycle = create_lifecycle()
    lifecycle.workout_started(create_workout())

    lifecycle.workout_finished(
        create_workout(
            status=WorkoutStatus.COMPLETED,
        )
    )

    assert lifecycle.active_workout_id is None
    assert lifecycle.last_decision is None


def test_finishing_non_active_workout_does_not_stop_active_session() -> None:
    lifecycle = create_lifecycle()
    lifecycle.workout_started(create_workout(workout_id="workout-1"))

    lifecycle.workout_finished(
        create_workout(
            workout_id="workout-2",
            status=WorkoutStatus.COMPLETED,
        )
    )

    assert lifecycle.active_workout_id == "workout-1"
