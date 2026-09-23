from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

from features.coaching.domain.live_coaching import (
    CoachingAction,
    HeartRateDeviationSeverity,
    HeartRateZoneStatus,
    LiveCoachingDecision,
    LiveCoachingPhaseEnding,
    LiveCoachingPhaseStarted,
    LiveCoachingWorkoutHalfway,
)
from features.telemetry.domain.health.heart_rate import HeartRateSample


class LiveCoachingEvent(BaseModel):
    """WebSocket-Event für eine relevante Herzfrequenz-Coaching-Entscheidung."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    type: Literal["coaching.decision"] = "coaching.decision"
    timestamp: datetime
    workout_id: str
    device_id: str
    action: CoachingAction
    zone_status: HeartRateZoneStatus
    heart_rate_bpm: int
    target_min_bpm: int
    target_max_bpm: int
    outside_target_seconds: float = Field(ge=0)
    deviation_bpm: int = Field(ge=0)
    deviation_severity: HeartRateDeviationSeverity
    reason: str

    @classmethod
    def from_decision(
        cls,
        *,
        workout_id: str,
        sample: HeartRateSample,
        decision: LiveCoachingDecision,
    ) -> "LiveCoachingEvent":
        return cls(
            timestamp=sample.timestamp,
            workout_id=workout_id,
            device_id=sample.device_id,
            action=decision.action,
            zone_status=decision.zone_status,
            heart_rate_bpm=decision.heart_rate_bpm,
            target_min_bpm=decision.target_min_bpm,
            target_max_bpm=decision.target_max_bpm,
            outside_target_seconds=decision.outside_target_seconds,
            deviation_bpm=decision.deviation_bpm,
            deviation_severity=decision.deviation_severity,
            reason=decision.reason,
        )


class LiveCoachingRuntimeEvent(BaseModel):
    """WebSocket-Event für sprachrelevante Runtime-Übergänge des Workouts."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    type: Literal["coaching.pause_started", "coaching.pause_ended"]
    timestamp: datetime
    workout_id: str


class LiveCoachingPhaseStartedEvent(BaseModel):
    """WebSocket-Event für den Beginn einer neuen Workout-Phase."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    type: Literal["coaching.phase_started"] = "coaching.phase_started"
    timestamp: datetime
    workout_id: str
    phase_index: int = Field(ge=0)
    phase_type: str
    duration_minutes: int = Field(gt=0)
    target_min_bpm: int
    target_max_bpm: int
    is_final_phase: bool

    @classmethod
    def from_phase_started(
        cls,
        *,
        workout_id: str,
        timestamp: datetime,
        phase_started: LiveCoachingPhaseStarted,
    ) -> "LiveCoachingPhaseStartedEvent":
        return cls(
            timestamp=timestamp,
            workout_id=workout_id,
            phase_index=phase_started.phase_index,
            phase_type=phase_started.phase_type,
            duration_minutes=phase_started.duration_minutes,
            target_min_bpm=phase_started.target_min_bpm,
            target_max_bpm=phase_started.target_max_bpm,
            is_final_phase=phase_started.is_final_phase,
        )


class LiveCoachingPhaseEndingEvent(BaseModel):
    """WebSocket-Event eine Minute vor Ende einer Workout-Phase."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    type: Literal["coaching.phase_ending"] = "coaching.phase_ending"
    timestamp: datetime
    workout_id: str
    phase_index: int = Field(ge=0)
    phase_type: str
    remaining_seconds: int = Field(gt=0)

    @classmethod
    def from_phase_ending(
        cls,
        *,
        workout_id: str,
        timestamp: datetime,
        phase_ending: LiveCoachingPhaseEnding,
    ) -> "LiveCoachingPhaseEndingEvent":
        return cls(
            timestamp=timestamp,
            workout_id=workout_id,
            phase_index=phase_ending.phase_index,
            phase_type=phase_ending.phase_type,
            remaining_seconds=phase_ending.remaining_seconds,
        )


class LiveCoachingWorkoutHalfwayEvent(BaseModel):
    """WebSocket-Event beim Erreichen der Workout-Halbzeit."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    type: Literal["coaching.workout_halfway"] = "coaching.workout_halfway"
    timestamp: datetime
    workout_id: str
    total_duration_minutes: int = Field(gt=0)

    @classmethod
    def from_halfway(
        cls,
        *,
        workout_id: str,
        timestamp: datetime,
        halfway: LiveCoachingWorkoutHalfway,
    ) -> "LiveCoachingWorkoutHalfwayEvent":
        return cls(
            timestamp=timestamp,
            workout_id=workout_id,
            total_duration_minutes=halfway.total_duration_minutes,
        )
