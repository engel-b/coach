from collections.abc import AsyncIterator
from typing import Protocol

from features.telemetry.domain.health.heart_rate import HeartRateSample


class HeartRateSource(Protocol):
    """
    Fachliche Schnittstelle für eine Quelle von Herzfrequenzdaten.

    Java-Vergleich:

        public interface HeartRateSource {
            Flow.Publisher<HeartRateSample> samples();
        }

    Wichtig:
    Diese Schnittstelle kennt absichtlich weder Bluetooth noch Bleak.

    Dadurch könnte eine HeartRateSource später genauso gut sein:
    - ein BLE-Brustgurt,
    - eine Testimplementierung,
    - ein aufgezeichnetes Workout,
    - ein anderes Gerät.
    """

    def samples(self) -> AsyncIterator[HeartRateSample]:
        """
        Liefert kontinuierlich neue Messwerte.

        AsyncIterator ist vereinfacht gesagt ein asynchroner Stream:
        Statt eine komplette Liste zurückzugeben, kommen die Werte
        nacheinander, sobald sie verfügbar sind.
        """
        ...
