import asyncio
import logging

from websockets.asyncio.client import connect
from websockets.exceptions import ConnectionClosed

from features.telemetry.api.contracts.telemetry import TelemetryMessage

logger = logging.getLogger(__name__)


class BackendWebSocketClient:
    """
    WebSocket-Client des Device Agents.

    Verantwortlichkeit:

        Device Agent
             │
             ▼
        BackendWebSocketClient
             │
             │ WebSocket
             ▼
        FastAPI Backend

    Der Client kümmert sich um:
    - Verbindungsaufbau
    - Reconnect
    - Versenden von Nachrichten

    Er kennt dagegen weder BLE noch den 808S.

    Java-Vergleich:
    Ein technischer Infrastructure Adapter für einen externen Dienst.
    """

    def __init__(
        self,
        uri: str,
        reconnect_delay_seconds: float = 2.0,
    ) -> None:
        self._uri = uri
        self._reconnect_delay_seconds = reconnect_delay_seconds

        # Queue zwischen Anwendung und Netzwerk.
        #
        # send() legt Nachrichten hinein.
        # run() nimmt sie heraus und überträgt sie.
        #
        # Vorteil:
        # Die Sensorverarbeitung muss nicht auf Netzwerk-I/O warten.
        self._queue: asyncio.Queue[TelemetryMessage] = asyncio.Queue()

    async def send(self, message: TelemetryMessage) -> None:
        """
        Stellt eine Nachricht zur Übertragung bereit.

        Die Methode führt bewusst nicht unmittelbar websocket.send()
        aus. Dadurch entkoppeln wir den Produzenten vom Netzwerk.
        """

        await self._queue.put(message)

    async def run(self) -> None:
        """
        Hält dauerhaft die Verbindung zum Backend.

        Wenn das Backend nicht läuft oder neu startet,
        versucht der Client automatisch einen Reconnect.
        """

        while True:
            try:
                logger.info("Connecting to backend: %s", self._uri)

                async with connect(self._uri) as websocket:
                    logger.info("Connected to backend")

                    while True:
                        message = await self._queue.get()

                        # by_alias=True sorgt dafür, dass im JSON
                        # "deviceId" statt "device_id" steht.
                        json_message = message.model_dump_json(
                            by_alias=True,
                        )

                        await websocket.send(json_message)

            except asyncio.CancelledError:
                # Der gesamte Device Agent wird beendet.
                # Cancellation niemals verschlucken.
                raise

            except (ConnectionClosed, OSError) as exc:
                logger.info(
                    "Backend connection unavailable: %s. Retrying in %.0f seconds ...",
                    exc,
                    self._reconnect_delay_seconds,
                )

                await asyncio.sleep(self._reconnect_delay_seconds)
