import asyncio
import logging
from collections.abc import AsyncIterator, Callable
from datetime import UTC, datetime

from bleak import BleakClient, BleakScanner
from bleak.backends.device import BLEDevice
from bleak.exc import BleakError

from adapters.bluetooth.heart_rate.constants import (
    HEART_RATE_MEASUREMENT_UUID,
    HEART_RATE_SERVICE_UUID,
)
from adapters.bluetooth.heart_rate.parser import parse_heart_rate
from domains.health.device import DeviceStatus, DeviceType
from domains.health.device_events import DeviceStatusChanged
from domains.health.heart_rate import HeartRateSample

logger = logging.getLogger(__name__)

DeviceStatusHandler = Callable[[DeviceStatusChanged], None]


class BleHeartRateAdapter:
    """
    BLE-Adapter für standardkonforme Heart-Rate-Sensoren.

    Ein Aufruf von samples() repräsentiert genau einen
    Discovery-/Connect-/Streaming-Lifecycle.

    Retry gehört bewusst nicht in diesen Adapter. Dafür ist der
    Device-Worker in apps.device_agent.lifecycle verantwortlich.
    """

    def __init__(
        self,
        status_handler: DeviceStatusHandler,
        scan_interval_seconds: float = 5.0,
    ) -> None:
        self._queue: asyncio.Queue[HeartRateSample] = asyncio.Queue()
        self._scan_interval_seconds = scan_interval_seconds
        self._status_handler = status_handler

    async def samples(self) -> AsyncIterator[HeartRateSample]:
        """
        Sucht genau einmal nach einem HR-Sensor und streamt dessen Samples.

        Ist kein Sensor verfügbar oder geht die Verbindung verloren,
        endet dieser Lifecycle mit einem BleakError.

        Der übergeordnete Device-Worker entscheidet anschließend,
        wann ein neuer Versuch gestartet wird.
        """

        self._publish_status(
            device_id="heart-rate",
            device_name="Heart Rate Sensor",
            status=DeviceStatus.SCANNING,
        )

        device = await self._find_device()

        if device is None:
            self._publish_status(
                device_id="heart-rate",
                device_name="Heart Rate Sensor",
                status=DeviceStatus.DISCONNECTED,
            )

            raise BleakError("Heart rate sensor not found")

        device_id = device.address
        device_name = device.name or "Heart Rate Sensor"

        self._publish_status(
            device_id=device_id,
            device_name=device_name,
            status=DeviceStatus.CONNECTING,
        )

        try:
            async with BleakClient(device) as client:
                self._publish_status(
                    device_id=device_id,
                    device_name=device_name,
                    status=DeviceStatus.CONNECTED,
                )

                def notification_handler(
                    _sender: object,
                    data: bytearray,
                ) -> None:
                    """
                    BLE Callback.

                    Bleak ruft diese Funktion auf, sobald der Gurt
                    einen neuen Heart Rate Measurement Wert sendet.

                    Der Callback macht absichtlich möglichst wenig:
                    1. Rohdaten parsen
                    2. Domain-Objekt erzeugen
                    3. in die Queue legen
                    """
                    bpm = parse_heart_rate(bytes(data))

                    sample = HeartRateSample(
                        device_id=device_id,
                        bpm=bpm,
                        timestamp=datetime.now(UTC),
                    )

                    self._queue.put_nowait(sample)

                await client.start_notify(
                    HEART_RATE_MEASUREMENT_UUID,
                    notification_handler,
                )

                try:
                    while client.is_connected:
                        try:
                            sample = await asyncio.wait_for(
                                self._queue.get(),
                                timeout=2.0,
                            )
                            yield sample

                        except TimeoutError:
                            # Keine HR-Notification innerhalb von zwei
                            # Sekunden ist nicht automatisch ein Fehler.
                            #
                            # Der Timeout dient hier nur dazu, regelmäßig
                            # client.is_connected erneut zu prüfen.
                            continue

                    raise BleakError(f"Heart rate sensor disconnected: {device_id}")

                finally:
                    if client.is_connected:
                        try:
                            await client.stop_notify(
                                HEART_RATE_MEASUREMENT_UUID,
                            )
                        except BleakError as exc:
                            logger.debug(
                                "Could not stop heart rate notifications cleanly for %s: %s",
                                device_id,
                                exc,
                            )

        finally:
            self._publish_status(
                device_id=device_id,
                device_name=device_name,
                status=DeviceStatus.DISCONNECTED,
            )

    async def _find_device(self) -> BLEDevice | None:
        """
        Führt genau einen BLE-Scan durch.

        Ein temporärer BlueZ-/Bleak-Fehler wird nicht hier in einer
        Retry-Schleife versteckt. Er wird an den Device-Worker
        weitergereicht.
        """

        try:
            discovered_devices = await BleakScanner.discover(
                timeout=10.0,
                return_adv=True,
            )

        except BleakError:
            logger.debug(
                "BLE scan for heart rate sensor currently unavailable",
            )
            raise

        for device, advertisement in discovered_devices.values():
            service_uuids = advertisement.service_uuids or []

            if HEART_RATE_SERVICE_UUID in [uuid.lower() for uuid in service_uuids]:
                return device

        return None

    def _publish_status(
        self,
        *,
        device_id: str,
        device_name: str,
        status: DeviceStatus,
    ) -> None:
        self._status_handler(
            DeviceStatusChanged(
                device_id=device_id,
                device_type=DeviceType.HEART_RATE,
                device_name=device_name,
                status=status,
                timestamp=datetime.now(UTC),
            )
        )
