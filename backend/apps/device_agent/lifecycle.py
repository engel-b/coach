import asyncio
import logging
from collections.abc import Awaitable, Callable

from bleak.exc import BleakError

logger = logging.getLogger(__name__)


# Eine Device-Operation repräsentiert genau einen Verbindungs-/Telemetry-Lauf.
#
# Java-Vergleich:
# ungefähr Supplier<CompletionStage<Void>>
DeviceOperation = Callable[[], Awaitable[None]]


async def run_device_worker(
    *,
    name: str,
    operation: DeviceOperation,
    retry_delay_seconds: float = 5.0,
) -> None:
    """
    Führt eine Device-Operation dauerhaft mit Retry aus.

    Erwartete technische Ausfälle wie:
    - Gerät ausgeschaltet
    - Gerät außer Reichweite
    - BLE-Verbindung verloren
    - temporärer I/O-Fehler

    beenden den Device Agent nicht.

    asyncio.CancelledError wird dagegen immer weitergereicht,
    damit der übergeordnete Shutdown sauber funktionieren kann.

    Unerwartete Exceptions werden absichtlich NICHT abgefangen.
    Dadurch bleiben echte Programmier- oder Integrationsfehler
    sichtbar und können den übergeordneten Task beenden.
    """

    while True:
        try:
            await operation()

            # Eine langlebige Device-Operation sollte normalerweise
            # nur durch Cancellation oder einen technischen Fehler enden.
            #
            # Falls sie regulär zurückkehrt, behandeln wir das ebenfalls
            # als vorübergehenden Ausfall und versuchen es erneut.
            logger.info(
                "%s stopped. Retrying in %.0f seconds ...",
                name,
                retry_delay_seconds,
            )

        except asyncio.CancelledError:
            # Shutdown niemals als normalen Fehler behandeln.
            raise

        except (BleakError, OSError, TimeoutError) as exc:
            logger.info(
                "%s unavailable: %s. Retrying in %.0f seconds ...",
                name,
                exc,
                retry_delay_seconds,
            )

        await asyncio.sleep(retry_delay_seconds)
