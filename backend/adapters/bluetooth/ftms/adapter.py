import asyncio
import logging
from collections.abc import AsyncIterator
from dataclasses import dataclass
from datetime import UTC, datetime

from bleak import BleakClient, BleakScanner
from bleak.backends.device import BLEDevice
from bleak.exc import BleakDBusError, BleakError

from adapters.bluetooth.discovery import BleDiscoveryCoordinator
from adapters.bluetooth.ftms.parser import (
    FtmsIndoorBikeData,
    FtmsParseError,
    parse_indoor_bike_data,
)
from domains.telemetry.bike import BikeTelemetry

logger = logging.getLogger(__name__)


FTMS_INDOOR_BIKE_DATA_UUID = "00002ad2-0000-1000-8000-00805f9b34fb"


@dataclass
class _BikeState:
    speed_kmh: float | None = None
    cadence_rpm: float | None = None
    distance_m: int | None = None
    power_w: int | None = None

    # Das MERACH meldet dieses Feld zwar, bei deinem mechanischen
    # Widerstandsrad aber konstant als 0. Daher geben wir es vorerst
    # nicht als echten Telemetriewert weiter.
    resistance: int | None = None


class FtmsBikeAdapter:
    """
    BLE-Adapter für standardisierte FTMS Indoor Bikes.

    Der Adapter ist absichtlich nicht MERACH-spezifisch.
    Das MRK-S26 ist lediglich eine konkrete FTMS-Implementierung.
    """

    def __init__(
        self,
        *,
        device_id: str,
        discovery: BleDiscoveryCoordinator,
        device_name: str | None = None,
        telemetry_timeout_seconds: float = 15.0,
    ) -> None:
        self._device_id = device_id
        self._device_name = device_name
        self._telemetry_timeout_seconds = telemetry_timeout_seconds
        self._discovery = discovery

    async def telemetry(self) -> AsyncIterator[BikeTelemetry]:
        """
        Verbindet sich mit dem Bike und liefert fortlaufend Telemetrie.

        Analog zu Java wäre dies am ehesten ein asynchroner Stream:
        Der Adapter produziert Werte, sobald BLE Notifications eintreffen.
        """
        device = await self._find_device()

        if device is None:
            raise BleakError(f"FTMS bike not found: {self._device_id}")

        queue: asyncio.Queue[BikeTelemetry] = asyncio.Queue()
        state = _BikeState()

        def notification_handler(
            _sender: object,
            raw_data: bytearray,
        ) -> None:
            try:
                parsed = parse_indoor_bike_data(bytes(raw_data))
            except FtmsParseError:
                logger.exception(
                    "Invalid FTMS Indoor Bike Data from %s: %s",
                    self._device_id,
                    bytes(raw_data).hex(" "),
                )
                return

            self._update_state(state, parsed)

            telemetry = BikeTelemetry(
                device_id=self._device_id,
                timestamp=datetime.now(UTC),
                speed_kmh=state.speed_kmh,
                cadence_rpm=state.cadence_rpm,
                distance_m=state.distance_m,
                power_w=state.power_w,
                # Mechanischer Widerstand:
                # 0 wäre semantisch irreführend.
                resistance=None,
            )

            queue.put_nowait(telemetry)

        logger.info(
            "Connecting FTMS bike %s (%s)",
            self._device_name or "unknown",
            self._device_id,
        )

        async with BleakClient(device) as client:
            logger.info(
                "FTMS bike connected: %s",
                self._device_id,
            )

            await client.start_notify(
                FTMS_INDOOR_BIKE_DATA_UUID,
                notification_handler,
            )

            try:
                while True:
                    try:
                        telemetry = await asyncio.wait_for(
                            queue.get(),
                            timeout=self._telemetry_timeout_seconds,
                        )

                    except TimeoutError as exc:
                        # Bleak kann eine Verbindung weiterhin als "connected"
                        # betrachten, obwohl vom Bike keine Notifications mehr
                        # eintreffen.
                        #
                        # In diesem Fall beenden wir diesen Verbindungs-Lifecycle
                        # bewusst mit BleakError. Der Device-Worker übernimmt
                        # anschließend den Retry und baut eine neue Verbindung auf.
                        raise BleakError(
                            f"FTMS bike connected but telemetry became silent: {self._device_id}"
                        ) from exc

                    yield telemetry

            except asyncio.CancelledError:
                logger.info(
                    "FTMS bike telemetry cancelled: %s",
                    self._device_id,
                )
                raise

            finally:
                if client.is_connected:
                    try:
                        await client.stop_notify(
                            FTMS_INDOOR_BIKE_DATA_UUID,
                        )
                    except BleakError as exc:
                        logger.debug(
                            "Could not stop FTMS notifications cleanly for %s: %s",
                            self._device_id,
                            exc,
                        )

        logger.info(
            "FTMS bike disconnected: %s",
            self._device_id,
        )

    async def _find_device(self) -> BLEDevice | None:
        async def discover() -> BLEDevice | None:
            return await BleakScanner.find_device_by_address(
                self._device_id,
                timeout=10.0,
            )

        try:
            return await self._discovery.run(discover)

        except BleakDBusError as exc:
            # BlueZ kann einen zweiten parallelen aktiven Scan ablehnen.
            #
            # Das passiert beispielsweise, wenn Heart-Rate- und Bike-Adapter
            # nahezu gleichzeitig nach ihren Geräten suchen.
            if exc.dbus_error == "org.bluez.Error.InProgress":
                logger.debug(
                    "FTMS discovery already in progress for %s",
                    self._device_id,
                )
                return None

            logger.warning(
                "FTMS discovery failed for %s: %s",
                self._device_id,
                exc,
            )
            return None

        except BleakError as exc:
            logger.warning(
                "FTMS discovery failed for %s: %s",
                self._device_id,
                exc,
            )
            return None

    @staticmethod
    def _update_state(
        state: _BikeState,
        update: FtmsIndoorBikeData,
    ) -> None:
        """
        Merge einer partiellen FTMS Notification in den letzten
        bekannten Gesamtzustand.

        Java-Denke:
        Das ist ungefähr ein kleiner zustandsbehafteter Aggregator,
        weil eine BLE Notification kein vollständiges DTO sein muss.
        """
        if update.speed_kmh is not None:
            state.speed_kmh = update.speed_kmh

        if update.cadence_rpm is not None:
            state.cadence_rpm = update.cadence_rpm

        if update.distance_m is not None:
            state.distance_m = update.distance_m

        if update.power_w is not None:
            state.power_w = update.power_w
