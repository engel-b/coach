from collections.abc import AsyncIterator
from typing import Protocol

from features.telemetry.domain.telemetry.bike import BikeTelemetry


class BikeSource(Protocol):
    """
    Port für eine Quelle von Fahrrad-Telemetriedaten.

    Vergleichbar mit einem Java-Interface:

        interface BikeSource {
            ...
        }

    Die Domain kennt nur diesen Vertrag.

    Implementierungen können später beispielsweise sein:
    - MerachBikeSource
    - QzBikeSource
    - SmartSpinBikeSource
    - FakeBikeSource für Tests
    """

    async def telemetry(
        self,
    ) -> AsyncIterator[BikeTelemetry]:
        """
        Liefert fortlaufend neue Telemetrie-Samples.
        """
        ...
