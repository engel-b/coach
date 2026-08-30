from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class BikeTelemetry:
    """
    Herstellerunabhängige Fahrrad-Telemetrie.

    Ein späterer MERACH-Adapter übersetzt seine BLE-Daten
    in genau dieses Modell.
    """

    device_id: str
    timestamp: datetime
    power_w: int | None = None
    cadence_rpm: float | None = None
    speed_kmh: float | None = None
    resistance: int | None = None
