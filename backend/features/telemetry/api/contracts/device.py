from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from features.telemetry.domain.health.device import DeviceStatus, DeviceType


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
        description="Eindeutige Kennung des Geräts innerhalb der Anwendung.",
        examples=["heart-rate-01"],
    )
    device_type: DeviceType = Field(
        serialization_alias="deviceType",
        description="Fachlicher Gerätetyp, beispielsweise Pulssensor oder Ergometer.",
    )
    device_name: str = Field(
        serialization_alias="deviceName",
        description="Anzeigename des Geräts.",
        examples=["MERACH Bike"],
    )
    status: DeviceStatus = Field(
        description="Aktueller Verbindungsstatus des Geräts.",
    )
    last_seen: datetime = Field(
        serialization_alias="lastSeen",
        description="Zeitpunkt der letzten vom Backend verarbeiteten Gerätemeldung.",
        examples=["2026-09-08T09:30:00Z"],
    )

    heart_rate_bpm: int | None = Field(
        default=None,
        serialization_alias="heartRateBpm",
        description="Zuletzt gemessener Puls in Schlägen pro Minute.",
        examples=[135],
    )
    speed_kmh: float | None = Field(
        default=None,
        serialization_alias="speedKmh",
        description="Zuletzt gemessene Geschwindigkeit in Kilometern pro Stunde.",
        examples=[24.5],
    )
    cadence_rpm: float | None = Field(
        default=None,
        serialization_alias="cadenceRpm",
        description="Zuletzt gemessene Trittfrequenz in Umdrehungen pro Minute.",
        examples=[82.0],
    )
    distance_m: int | None = Field(
        default=None,
        serialization_alias="distanceM",
        description="Vom Gerät gemeldete Distanz in ganzen Metern.",
        examples=[3500],
    )
    power_w: int | None = Field(
        default=None,
        serialization_alias="powerW",
        description="Zuletzt gemessene Leistung in Watt.",
        examples=[145],
    )
    resistance: int | None = Field(
        default=None,
        description=(
            "Zuletzt gemeldeter Widerstandswert. Die Bedeutung und "
            "Skalierung können vom jeweiligen Geräteadapter abhängen."
        ),
        examples=[12],
    )
