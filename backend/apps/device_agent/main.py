import asyncio
import logging
import signal

from adapters.bluetooth.ble_heart_rate_adapter import BleHeartRateAdapter
from adapters.bluetooth.ftms.bike_adapter import FtmsBikeAdapter
from adapters.websocket.backend_client import BackendWebSocketClient
from apps.device_agent.lifecycle import run_device_worker
from contracts.telemetry import TelemetryMessage
from domains.health.device_events import DeviceStatusChanged

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

logger = logging.getLogger(__name__)


BACKEND_WEBSOCKET_URI = "ws://127.0.0.1:8000/ws/device-agent"

BIKE_ADDRESS = "24:00:0C:A0:9A:95"
BIKE_NAME = "MRK-S26-1AA7"


async def consume_heart_rate(
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

    Java-Vergleich grob:
        Ein länger laufender Future/Task, den der übergeordnete
        Service beim Shutdown gezielt canceln kann.
    """

    async for sample in heart_rate_source.samples():
        logger.info(
            "Heart rate: %d bpm",
            sample.bpm,
        )

        message = TelemetryMessage(
            type="heart_rate.sample",
            timestamp=sample.timestamp,
            device_id=sample.device_id,
            payload={
                "bpm": sample.bpm,
            },
        )

        await backend_client.send(message)


async def consume_bike_telemetry(
    bike_source: FtmsBikeAdapter,
    backend_client: BackendWebSocketClient,
) -> None:
    """
    Konsumiert die Telemetrie des Bikes.

    Der eigentliche Retry-Lifecycle liegt bewusst nicht mehr
    in dieser Funktion, sondern zentral in run_device_worker().

    Dadurch können HR und Bike später dieselbe Retry-Policy
    verwenden.

    Java-Vergleich:
    Diese Funktion beschreibt die eigentliche Arbeit.
    run_device_worker() entspricht dem langlebigen Executor,
    der diese Arbeit bei technischen Fehlern erneut startet.
    """

    async def consume_once() -> None:
        """
        Führt genau einen FTMS-Verbindungs-/Telemetry-Lauf aus.

        FtmsBikeAdapter.telemetry() endet bei einem BLE-Fehler
        mit einer Exception. run_device_worker() übernimmt danach
        den Retry.
        """

        async for telemetry in bike_source.telemetry():
            logger.info(
                "Bike: speed=%s km/h cadence=%s rpm power=%s W",
                telemetry.speed_kmh,
                telemetry.cadence_rpm,
                telemetry.power_w,
            )

            message = TelemetryMessage(
                type="bike.telemetry",
                timestamp=telemetry.timestamp,
                device_id=telemetry.device_id,
                payload={
                    "speedKmh": telemetry.speed_kmh,
                    "cadenceRpm": telemetry.cadence_rpm,
                    "powerW": telemetry.power_w,
                    "resistance": telemetry.resistance,
                },
            )

            await backend_client.send(message)

    await run_device_worker(
        name="FTMS bike",
        operation=consume_once,
        retry_delay_seconds=5.0,
    )


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

    backend_client = BackendWebSocketClient(
        uri=BACKEND_WEBSOCKET_URI,
    )

    # Dieses Event ist unser internes Shutdown-Signal.
    #
    # Der eigentliche Unix-Signal-Handler führt bewusst keine
    # asynchrone Arbeit aus. Er setzt lediglich dieses Event.
    shutdown_event = asyncio.Event()

    loop = asyncio.get_running_loop()

    def request_shutdown() -> None:
        """
        Fordert einen kontrollierten Shutdown an.

        Diese Funktion wird vom asyncio Event Loop aufgerufen,
        sobald SIGINT oder SIGTERM empfangen wurde.
        """

        if shutdown_event.is_set():
            return

        logger.info(
            "Device Agent shutdown requested",
        )

        shutdown_event.set()

    for shutdown_signal in (
        signal.SIGINT,
        signal.SIGTERM,
    ):
        loop.add_signal_handler(
            shutdown_signal,
            request_shutdown,
        )

    def on_device_status(
        event: DeviceStatusChanged,
    ) -> None:
        """
        Callback des BLE-Adapters.

        Der BLE-Adapter kennt weder WebSocket noch Backend.
        Hier übersetzt der Device Agent das Domain Event in
        unsere TelemetryMessage.
        """

        message = TelemetryMessage(
            type="device.status_changed",
            timestamp=event.timestamp,
            device_id=event.device_id,
            payload={
                "deviceType": event.device_type.value,
                "deviceName": event.device_name,
                "status": event.status.value,
            },
        )

        asyncio.create_task(
            backend_client.send(message),
        )

    heart_rate_source = BleHeartRateAdapter(
        status_handler=on_device_status,
    )

    bike_source = FtmsBikeAdapter(
        device_id=BIKE_ADDRESS,
        device_name=BIKE_NAME,
    )

    # Beide langlebigen Komponenten laufen als eigene Tasks:
    #
    # 1. WebSocket-Verbindung zum Backend
    # 2. BLE-Sensorverarbeitung
    backend_task = asyncio.create_task(
        backend_client.run(),
        name="backend-websocket",
    )

    heart_rate_task = asyncio.create_task(
        consume_heart_rate(
            heart_rate_source,
            backend_client,
        ),
        name="heart-rate",
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
        name="shutdown-wait",
    )

    logger.info(
        "Starting Health Coach Device Agent",
    )

    try:
        # Wir warten auf das erste von zwei Ereignissen:
        #
        # - Shutdown wurde angefordert
        # - Heart-Rate-Verarbeitung ist unerwartet beendet
        #
        # Java-Vergleich grob:
        #
        # CompletableFuture.anyOf(...)
        done, _pending = await asyncio.wait(
            {
                heart_rate_task,
                bike_task,
                shutdown_task,
            },
            return_when=asyncio.FIRST_COMPLETED,
        )

        # Normalerweise wird shutdown_task zuerst fertig.
        #
        # Falls dagegen der Heart-Rate-Task von selbst endet,
        # prüfen wir, ob dort eine Exception aufgetreten ist.
        for task in (
            heart_rate_task,
            bike_task,
        ):
            if task not in done:
                continue

            if task.cancelled():
                continue

            exception = task.exception()

            if exception is not None:
                raise exception

            raise RuntimeError(f"Device Agent task ended unexpectedly: {task.get_name()}")

    finally:
        logger.info(
            "Stopping Device Agent ...",
        )

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

        # Falls wir nicht wegen eines Shutdown-Signals hier
        # gelandet sind, wartet dieser Task möglicherweise
        # noch auf das Event.
        shutdown_task.cancel()

        await asyncio.gather(
            heart_rate_task,
            bike_task,
            shutdown_task,
            return_exceptions=True,
        )

        # Erst nachdem BLE beendet wurde, schließen wir die
        # Verbindung zum Backend.
        backend_task.cancel()

        await asyncio.gather(
            backend_task,
            return_exceptions=True,
        )

        # Signal-Handler wieder entfernen.
        #
        # Für unseren heutigen Einzelprozess wäre das nicht
        # zwingend erforderlich, macht aber den Lebenszyklus
        # vollständig symmetrisch.
        for shutdown_signal in (
            signal.SIGINT,
            signal.SIGTERM,
        ):
            loop.remove_signal_handler(
                shutdown_signal,
            )

        logger.info(
            "Device Agent stopped cleanly",
        )


def main() -> None:
    """
    Synchroner Bootstrap des Device Agents.

    asyncio.run() erzeugt und verwaltet den Event Loop.
    Die eigentliche Signalbehandlung findet jetzt innerhalb
    von run() statt.
    """

    asyncio.run(run())


if __name__ == "__main__":
    main()
