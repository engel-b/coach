from dataclasses import dataclass
from datetime import datetime

from features.telemetry.domain.health.device import DeviceStatus, DeviceType


@dataclass(frozen=True)
class DeviceStatusChanged:
    """
    Meldung über den aktuellen Zustand eines Geräts.

    Beispiel:

        DeviceStatusChanged(
            device_id="AA:BB:CC:DD:EE:FF",
            device_type=DeviceType.HEART_RATE,
            device_name="808S",
            status=DeviceStatus.CONNECTED,
            timestamp=...,
        )

    Später kann dieses Event gleichzeitig verschiedene Interessenten haben:

        Device Agent
             │
             ├──> WebSocket / Frontend
             ├──> Logging
             └──> Monitoring

    Java-Vergleich:
    Im Prinzip ein unveränderliches Domain Event / Record.
    """

    device_id: str
    device_type: DeviceType
    device_name: str
    status: DeviceStatus
    timestamp: datetime
