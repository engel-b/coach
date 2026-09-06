from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from domains.health.device import DeviceStatus, DeviceType


class DeviceResponse(BaseModel):
    """
    REST-Repräsentation des aktuellen Gerätezustands.

    Intern verwendet Python snake_case.
    Die HTTP-API liefert bewusst camelCase.
    """

    model_config = ConfigDict(
        populate_by_name=True,
    )

    device_id: str = Field(
        serialization_alias="deviceId",
    )
    device_type: DeviceType = Field(
        serialization_alias="deviceType",
    )
    device_name: str = Field(
        serialization_alias="deviceName",
    )
    status: DeviceStatus
    last_seen: datetime = Field(
        serialization_alias="lastSeen",
    )

    heart_rate_bpm: int | None = Field(
        default=None,
        serialization_alias="heartRateBpm",
    )

    speed_kmh: float | None = Field(
        default=None,
        serialization_alias="speedKmh",
    )
    cadence_rpm: float | None = Field(
        default=None,
        serialization_alias="cadenceRpm",
    )
    distance_m: int | None = Field(
        default=None,
        serialization_alias="distanceM",
    )
    power_w: int | None = Field(
        default=None,
        serialization_alias="powerW",
    )
    resistance: int | None = None
