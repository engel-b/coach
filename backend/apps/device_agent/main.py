from __future__ import annotations

import asyncio
import logging
import signal

from bleak.exc import BleakError

from adapters.bluetooth.discovery import BleDiscoveryCoordinator
from adapters.bluetooth.ftms.bike_adapter import FtmsBikeAdapter
from adapters.bluetooth.heart_rate_adapter import BleHeartRateAdapter
from apps.device_agent.backend_websocket_client import BackendWebSocketClient


logger = logging.getLogger(__name__)


BACKEND_WEBSOCKET_URI = "ws://127.0.0.1:8000/ws/device-agent"

HEART_RATE_DEVICE_ID = "D3:12:DD:56:74:7E"
BIKE_DEVICE_ID = "24:00:0C:A0:9A:95"


async def consume_heart_rate_telemetry(
    heart_rate_source: BleHeartRateAdapter,
    backend_client: BackendWebSocketClient,
) -> None:
    """
    Konsumiert dauerhaft die Herzfrequenzwerte des BLE-Adapters.

    Diese Verarbeitung läuft bewusst in einem eigenen asyncio-Task.
    Dadurch können wir sie beim Shutdown gezielt abbrechen.

    Die Cancellation läuft anschließend bis in
    BleHeartRateAdapter.samples() hinein. Dort sorgt der bestehende
    async-with-Block des BleakClient für das Aufräumen der
    BLE-Verbindung.
    """

    while True:
        try:
            async for telemetry in heart_rate_source.telemetry():
                await backend_client.send_heart_rate(telemetry)

        except asyncio.CancelledError:
            raise

        except BleakError as exc:
            logger.info(
                "Heart-rate sensor unavailable: %s; retrying",
                exc,
            )
            await asyncio.sleep(5.0)


async def consume_bike_telemetry(
    bike_source: FtmsBikeAdapter,
    backend_client: BackendWebSocketClient,
) -> None:
    """
    Konsumiert dauerhaft die Telemetrie des Bikes.

    Das Bike darf beim Start ausgeschaltet oder vorübergehend
    nicht erreichbar sein. Ein BLE-Verbindungsfehler beendet
    deshalb nicht den gesamten Device Agent.

    Stattdessen versuchen wir nach kurzer Pause erneut,
    eine Verbindung aufzubauen.

    Java-Vergleich:
        Ähnlich einem langlebigen Worker mit Retry-Schleife
        um einen technischen Infrastructure Adapter.
    """

    while True:
        try:
            async for telemetry in bike_source.telemetry():
                logger.debug(
                    "Bike: speed=%s cadence=%s power=%s",
                    telemetry.speed_kmh,
                    telemetry.cadence_rpm,
                    telemetry.power_w,
                )

                await backend_client.send_bike_telemetry(telemetry)

        except asyncio.CancelledError:
            # Shutdown des Device Agents.
            #
            # Cancellation niemals als normalen Fehler behandeln.
            raise

        except BleakError as exc:
            # Ein ausgeschaltetes Bike, ein Verbindungsabbruch oder
            # ein vorübergehend nicht möglicher BLE-Scan ist ein
            # normaler Betriebszustand.
            logger.info(
                "FTMS bike unavailable: %s; retrying",
                exc,
            )
            await asyncio.sleep(5.0)


async def run() -> None:
    """
    Hauptprozess des Device Agents.

    Wir haben zwei technische Seiten:

        BLE                           WebSocket
         │                               │
         ▼                               ▼
    HeartRateAdapter             BackendWebSocketClient
         │                               │
         └──────── Device Agent ─────────┘

    SIGINT (Ctrl+C) und SIGTERM führen beide über denselben
    kontrollierten Shutdown-Pfad.
    """
    shutdown_event = asyncio.Event()

    loop = asyncio.get_running_loop()

    def request_shutdown() -> None:
        """
        Fordert einen kontrollierten Shutdown an.

        Diese Funktion wird vom asyncio Event Loop aufgerufen,
        sobald SIGINT oder SIGTERM empfangen wurde.
        """
        logger.info("Device Agent shutdown requested")
        shutdown_event.set()

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(
            sig,
            request_shutdown,
        )

    #
    # One shared BLE discovery coordinator for the complete Device Agent.
    #
    # This is the important part of the change:
    # both adapters use the same asyncio.Lock internally and therefore
    # cannot start BlueZ discovery at the same time.
    #
    discovery = BleDiscoveryCoordinator()

    heart_rate_source = BleHeartRateAdapter(
        device_id=HEART_RATE_DEVICE_ID,
        discovery=discovery,
    )

    bike_source = FtmsBikeAdapter(
        device_id=BIKE_DEVICE_ID,
        discovery=discovery,
    )

    backend_client = BackendWebSocketClient(
        BACKEND_WEBSOCKET_URI,
    )

    backend_task = asyncio.create_task(
        backend_client.run(),
        name="backend-websocket",
    )

    heart_rate_task = asyncio.create_task(
        consume_heart_rate_telemetry(
            heart_rate_source,
            backend_client,
        ),
        name="heart-rate-telemetry",
    )

    bike_task = asyncio.create_task(
        consume_bike_telemetry(
            bike_source,
            backend_client,
        ),
        name="bike-telemetry",
    )

    # Dieser Task wird fertig, sobald SIGINT oder SIGTERM
    # unser shutdown_event setzt.
    shutdown_task = asyncio.create_task(
        shutdown_event.wait(),
        name="shutdown",
    )

    tasks = {
        backend_task,
        heart_rate_task,
        bike_task,
        shutdown_task,
    }

    try:
        done, _ = await asyncio.wait(
            tasks,
            return_when=asyncio.FIRST_COMPLETED,
        )

        #
        # Normally only shutdown_task completes on its own.
        #
        # If one of the long-running tasks terminates unexpectedly, surface
        # that instead of silently continuing with a half-dead Device Agent.
        #
        for task in done:
            if task is shutdown_task:
                continue

            exception = task.exception()

            if exception is not None:
                raise exception

            raise RuntimeError(
                f"Device Agent task terminated unexpectedly: "
                f"{task.get_name()}"
            )

    finally:
        logger.info("Stopping Device Agent ...")

        # Zuerst stoppen wir die BLE-Seite.
        #
        # Dadurch erhält BleHeartRateAdapter.samples()
        # eine asyncio.CancelledError.
        #
        # Der Adapter reicht diese bereits korrekt weiter.
        # Anschließend wird sein:
        #
        #     async with BleakClient(...)
        #
        # verlassen und Bleak kann Notifications und
        # BLE-Verbindung kontrolliert schließen.
        heart_rate_task.cancel()
        bike_task.cancel()

        await asyncio.gather(
            heart_rate_task,
            bike_task,
            return_exceptions=True,
        )

        # Erst nachdem BLE beendet wurde, schließen wir die
        # Verbindung zum Backend.
        backend_task.cancel()

        # Falls wir nicht wegen eines Shutdown-Signals hier
        # gelandet sind, wartet dieser Task möglicherweise
        # noch auf das Event.
        shutdown_task.cancel()

        await asyncio.gather(
            backend_task,
            shutdown_task,
            return_exceptions=True,
        )

        # Signal-Handler wieder entfernen.
        #
        # Für unseren heutigen Einzelprozess wäre das nicht
        # zwingend erforderlich, macht aber den Lebenszyklus
        # vollständig symmetrisch.
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.remove_signal_handler(sig)

        logger.info("Device Agent stopped cleanly")


def main() -> None:
    """
    Synchroner Bootstrap des Device Agents.

    asyncio.run() erzeugt und verwaltet den Event Loop.
    Die eigentliche Signalbehandlung findet jetzt innerhalb
    von run() statt.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    asyncio.run(run())


if __name__ == "__main__":
    main()