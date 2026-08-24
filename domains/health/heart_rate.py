from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class HeartRateSample:
    """
    Ein einzelner Herzfrequenz-Messwert.

    Java-Vergleich:

        public record HeartRateSample(
            String deviceId,
            Instant timestamp,
            int bpm
        ) {}

    frozen=True bedeutet:
    Nach dem Erzeugen ist das Objekt unveränderlich.

    Das ist für Messdaten sehr praktisch, weil ein einmal empfangener
    Messwert später nicht versehentlich verändert werden sollte.
    """

    device_id: str
    timestamp: datetime
    bpm: int
