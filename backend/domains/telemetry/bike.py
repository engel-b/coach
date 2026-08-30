from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class BikeTelemetry:
    """
    Herstellerunabhängiger Zustand eines Fahrrads.

    Wichtig:
    Dieses Modell kennt absichtlich weder MERACH noch BLE.

    Ein späterer MERACH-Adapter hat die Aufgabe, die proprietären
    Gerätedaten in dieses allgemeine Domain-Modell zu übersetzen.
    """

    device_id: str
    timestamp: datetime

    power_w: int | None = None
    cadence_rpm: float | None = None
    speed_kmh: float | None = None
    resistance: int | None = None
