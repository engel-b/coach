import asyncio
import logging
from collections.abc import AsyncIterator
from dataclasses import dataclass
from datetime import UTC, datetime

from bleak import BleakClient, BleakScanner
from bleak.backends.device import BLEDevice
from bleak.exc import BleakDBusError, BleakError

from adapters.bluetooth.ftms.indoor_bike_parser import (
    FtmsIndoorBikeData,
    FtmsParseError,
    parse_indoor_bike_data,
)

# Den Import ggf. an den tatsächlichen Ort deines bereits vorhandenen
# Domain-Typs anpassen.
from domains.telemetry.bike import BikeTelemetry

logger = logging.getLogger(__name__)


FTMS_INDOOR_BIKE_DATA_UUID = "00002ad2-0000-1000-8000-00805f9b34fb"


@dataclass
class _BikeState:
    speed_kmh: float | None = None
    cadence_rpm: float | None = None
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
        device_name: str | None = None,
    ) -> None:
        self._device_id = device_id
        self._device_name = device_name

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
                    yield await queue.get()

            except asyncio.CancelledError:
                logger.info(
                    "FTMS bike telemetry cancelled: %s",
                    self._device_id,
                )
                raise

            finally:
                if client.is_connected:
                    try:
                        await client.stop_notify(FTMS_INDOOR_BIKE_DATA_UUID)
                    except BleakError:
                        logger.exception("Could not stop FTMS notifications cleanly")

        logger.info(
            "FTMS bike disconnected: %s",
            self._device_id,
        )

    async def _find_device(self) -> BLEDevice | None:
        try:
            return await BleakScanner.find_device_by_address(
                self._device_id,
                timeout=10.0,
            )

        except BleakDBusError as exc:
            # BlueZ kann einen zweiten parallelen aktiven Scan ablehnen.
            #
            # Das passiert beispielsweise, wenn Heart-Rate- und Bike-Adapter
            # nahezu gleichzeitig nach ihren Geräten suchen.
            if exc.dbus_error == "org.bluez.Error.InProgress":
                logger.debug(
                    "BLE scan already in progress while looking for FTMS bike %s",
                    self._device_id,
                )
                return None

            logger.warning(
                "BLE discovery failed for FTMS bike %s: %s",
                self._device_id,
                exc,
            )
            return None

        except BleakError as exc:
            logger.warning(
                "BLE discovery failed for FTMS bike %s: %s",
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

        if update.power_w is not None:
            state.power_w = update.power_w
