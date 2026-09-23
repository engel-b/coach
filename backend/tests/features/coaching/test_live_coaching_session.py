from datetime import UTC, datetime, timedelta

import pytest

from features.coaching.domain.live_coaching import (
    CoachingAction,
    LiveCoachingRules,
)
from features.coaching.service.heart_rate_deviation_tracker import (
    HeartRateDeviationTracker,
)
from features.coaching.service.live_coaching_engine import LiveCoachingEngine
from features.coaching.service.live_coaching_service import LiveCoachingService
from features.coaching.service.live_coaching_session import LiveCoachingSession
from features.telemetry.domain.health.heart_rate import HeartRateSample
from features.telemetry.domain.telemetry.bike import BikeTelemetry
from features.training.domain.recommendation import (
    WorkoutPhase,
    WorkoutPhaseType,
)
from features.workout.domain.runtime import WorkoutRuntimeState
from features.workout.domain.session import WorkoutSession, WorkoutStatus


def create_workout(
    *,
    status: WorkoutStatus = WorkoutStatus.RUNNING,
) -> WorkoutSession:
    return WorkoutSession(
        id="workout-1",
        person_id=1,
        started_at=datetime.now(UTC),
        status=status,
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


def create_session(
    workout: WorkoutSession | None = None,
) -> LiveCoachingSession:
    coaching_service = LiveCoachingService(
        deviation_tracker=HeartRateDeviationTracker(),
        coaching_engine=LiveCoachingEngine(
            rules=LiveCoachingRules(
                deviation_seconds_before_action=20.0,
            )
        ),
    )

    return LiveCoachingSession(
        workout=workout or create_workout(),
        coaching_service=coaching_service,
    )


def test_warm_up_uses_warm_up_heart_rate_target() -> None:
    session = create_session()

    timestamp = datetime.now(UTC)

    decision = session.handle_heart_rate(
        HeartRateSample(
            device_id="heart-rate-1",
            timestamp=timestamp,
            bpm=130,
        )
    )

    assert decision is not None
    assert decision.target_min_bpm == 100
    assert decision.target_max_bpm == 120


def test_main_phase_uses_main_heart_rate_target() -> None:
    session = create_session()

    session.update_elapsed_seconds(300)

    decision = session.handle_heart_rate(
        HeartRateSample(
            device_id="heart-rate-1",
            timestamp=datetime.now(UTC),
            bpm=135,
        )
    )

    assert decision is not None
    assert decision.target_min_bpm == 125
    assert decision.target_max_bpm == 145
    assert decision.action is CoachingAction.NONE


def test_sustained_high_heart_rate_in_main_phase_reduces_intensity() -> None:
    session = create_session()
    session.update_elapsed_seconds(300)

    start = datetime.now(UTC)

    first = session.handle_heart_rate(
        HeartRateSample(
            device_id="heart-rate-1",
            timestamp=start,
            bpm=150,
        )
    )

    second = session.handle_heart_rate(
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


def test_no_coaching_decision_after_planned_workout_duration() -> None:
    session = create_session()

    session.update_elapsed_seconds(1800)

    decision = session.handle_heart_rate(
        HeartRateSample(
            device_id="heart-rate-1",
            timestamp=datetime.now(UTC),
            bpm=160,
        )
    )

    assert decision is None


def test_elapsed_seconds_must_not_move_backwards() -> None:
    session = create_session()

    session.update_elapsed_seconds(300)

    with pytest.raises(
        ValueError,
        match="elapsed_seconds must not move backwards",
    ):
        session.update_elapsed_seconds(299)


def test_finished_workout_cannot_create_live_coaching_session() -> None:
    workout = create_workout(
        status=WorkoutStatus.COMPLETED,
    )

    with pytest.raises(
        ValueError,
        match="live coaching requires a running workout",
    ):
        create_session(workout)


def test_paused_session_ignores_heart_rate_and_resets_deviation() -> None:
    session = create_session()
    session.update_elapsed_seconds(300)

    start = datetime.now(UTC)

    session.handle_heart_rate(
        HeartRateSample(
            device_id="heart-rate-1",
            timestamp=start,
            bpm=150,
        )
    )

    session.update_runtime_state(WorkoutRuntimeState.PAUSED)

    paused_decision = session.handle_heart_rate(
        HeartRateSample(
            device_id="heart-rate-1",
            timestamp=start + timedelta(seconds=30),
            bpm=150,
        )
    )

    session.update_runtime_state(WorkoutRuntimeState.RUNNING)

    resumed_decision = session.handle_heart_rate(
        HeartRateSample(
            device_id="heart-rate-1",
            timestamp=start + timedelta(seconds=31),
            bpm=150,
        )
    )

    assert paused_decision is None
    assert resumed_decision is not None
    assert resumed_decision.action is CoachingAction.NONE
    assert resumed_decision.outside_target_seconds == 0.0


def test_finish_window_and_overtime_ignore_heart_rate() -> None:
    session = create_session()

    for runtime_state in (
        WorkoutRuntimeState.FINISH_WINDOW,
        WorkoutRuntimeState.OVERTIME,
    ):
        session.update_runtime_state(runtime_state)

        decision = session.handle_heart_rate(
            HeartRateSample(
                device_id="heart-rate-1",
                timestamp=datetime.now(UTC),
                bpm=180,
            )
        )

        assert decision is None


def test_structure_events_are_emitted_when_thresholds_are_crossed() -> None:
    from features.coaching.domain.live_coaching import (
        LiveCoachingPhaseEnding,
        LiveCoachingWorkoutHalfway,
    )

    session = create_session()

    warm_up_ending = session.update_elapsed_seconds(242)
    assert len(warm_up_ending) == 1
    assert isinstance(warm_up_ending[0], LiveCoachingPhaseEnding)
    assert warm_up_ending[0].phase_index == 0

    session.update_elapsed_seconds(899)
    halfway = session.update_elapsed_seconds(901)
    assert len(halfway) == 1
    assert isinstance(halfway[0], LiveCoachingWorkoutHalfway)


def test_final_phase_started_is_marked_as_final() -> None:
    from features.coaching.domain.live_coaching import LiveCoachingPhaseStarted

    session = create_session()
    session.update_elapsed_seconds(1499)
    events = session.update_elapsed_seconds(1500)

    phase_started = next(event for event in events if isinstance(event, LiveCoachingPhaseStarted))
    assert phase_started.phase_type == "cool_down"
    assert phase_started.is_final_phase is True


def test_structure_event_is_not_repeated_after_threshold_was_crossed() -> None:
    session = create_session()

    first = session.update_elapsed_seconds(242)
    second = session.update_elapsed_seconds(250)

    assert first
    assert second == ()


def test_main_phase_heart_rate_summary_is_aggregated() -> None:
    session = create_session()
    session.update_elapsed_seconds(300)
    timestamp = datetime.now(UTC)

    for offset, bpm in enumerate((120, 130, 140, 150)):
        session.handle_heart_rate(
            HeartRateSample(
                device_id="heart-rate-1",
                timestamp=timestamp + timedelta(seconds=offset),
                bpm=bpm,
            )
        )

    summary = session.heart_rate_summary()

    assert summary is not None
    assert summary.sample_count == 4
    assert summary.average_bpm == 135
    assert summary.max_bpm == 150
    assert summary.below_target_percent == 25
    assert summary.in_target_percent == 50
    assert summary.above_target_percent == 25


def test_warm_up_samples_are_not_in_main_phase_summary() -> None:
    session = create_session()
    session.handle_heart_rate(
        HeartRateSample(
            device_id="heart-rate-1",
            timestamp=datetime.now(UTC),
            bpm=110,
        )
    )

    assert session.heart_rate_summary() is None


def test_main_phase_bike_summary_is_aggregated() -> None:
    session = create_session()
    session.update_elapsed_seconds(300)
    timestamp = datetime.now(UTC)

    session.handle_bike_telemetry(
        BikeTelemetry(
            device_id="bike-1",
            timestamp=timestamp,
            power_w=100,
            cadence_rpm=70.0,
        )
    )
    session.handle_bike_telemetry(
        BikeTelemetry(
            device_id="bike-1",
            timestamp=timestamp + timedelta(seconds=1),
            power_w=140,
            cadence_rpm=80.0,
        )
    )

    summary = session.bike_summary()

    assert summary is not None
    assert summary.power_sample_count == 2
    assert summary.average_power_w == 120
    assert summary.cadence_sample_count == 2
    assert summary.average_cadence_rpm == 75.0


def test_bike_samples_outside_main_phase_are_not_aggregated() -> None:
    session = create_session()
    session.handle_bike_telemetry(
        BikeTelemetry(
            device_id="bike-1",
            timestamp=datetime.now(UTC),
            power_w=120,
            cadence_rpm=75.0,
        )
    )

    assert session.bike_summary() is None
