from dataclasses import dataclass
from datetime import datetime

from domains.health.device import DeviceStatus, DeviceType


@dataclass(frozen=True)
class DeviceState:
    """
    Aktuell bekannter Laufzeitzustand eines Geräts.

    Dies ist bewusst kein persistiertes Domain-Objekt.

    Beispiel:

        808S
        ├── connected
        ├── last_seen = ...
        └── heart_rate = 82
    """

    device_id: str
    device_type: DeviceType
    device_name: str
    status: DeviceStatus
    last_seen: datetime

    heart_rate_bpm: int | None = None

    speed_kmh: float | None = None
    cadence_rpm: float | None = None
    distance_m: int | None = None
    power_w: int | None = None
    resistance: int | None = None
