from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

from features.coaching.domain.live_coaching import (
    CoachingAction,
    HeartRateZoneStatus,
    LiveCoachingDecision,
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
