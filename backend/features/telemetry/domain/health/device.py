from dataclasses import dataclass
from enum import StrEnum


class DeviceType(StrEnum):
    """
    Fachliche Kategorien von Geräten.

    StrEnum ist Enum + String. Dadurch lässt sich der Wert später
    unkompliziert als JSON übertragen.

    Java ungefähr:

        enum DeviceType {
            HEART_RATE,
            BIKE,
            SCALE
        }
    """

    HEART_RATE = "heart_rate"
    BIKE = "bike"
    SCALE = "scale"


class DeviceStatus(StrEnum):
    """
    Aktueller Verbindungszustand eines Geräts.

    Wichtig:
    DISCONNECTED ist kein Fehler. Ein Brustgurt, der gerade nicht
    getragen wird, ist ein völlig normaler Systemzustand.
    """

    DISCONNECTED = "disconnected"
    SCANNING = "scanning"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"


@dataclass(frozen=True)
class Device:
    """
    Fachliche Beschreibung eines physischen Geräts.

    Java ungefähr:

        public record Device(
            String id,
            DeviceType type,
            String name
        ) {}

    Der Status gehört bewusst NICHT hier hinein:
    Device beschreibt das Gerät; DeviceStatusChanged beschreibt
    Veränderungen seines Laufzeitzustands.
    """

    id: str
    type: DeviceType
    name: str
