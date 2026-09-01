import asyncio
import logging
from collections.abc import AsyncIterator, Callable
from datetime import UTC, datetime

from bleak import BleakClient
from bleak.backends.device import BLEDevice
from bleak.exc import BleakError

from adapters.bluetooth.heart_rate_constants import (
    HEART_RATE_MEASUREMENT_UUID,
    HEART_RATE_SERVICE_UUID,
)
from adapters.bluetooth.heart_rate_parser import parse_heart_rate
from domains.health.device import DeviceStatus, DeviceType
from domains.health.device_events import DeviceStatusChanged
from domains.health.heart_rate import HeartRateSample

logger = logging.getLogger(__name__)

# Python Type Alias.
#
# Java-Vergleich ungefähr:
#
#     Consumer<DeviceStatusChanged>
#
# Der Adapter meldet Statusänderungen nach außen, ohne zu wissen,
# was der Empfänger später damit macht.
DeviceStatusHandler = Callable[[DeviceStatusChanged], None]


class BleHeartRateAdapter:
    """
    Adapter für standardisierte Bluetooth-LE-Herzfrequenzsensoren.

    Architektur:

        Domain
          ↑
        HeartRateSource
          ↑
        BleHeartRateAdapter
          ↓
        Bleak
          ↓
        BlueZ
          ↓
        808S

    Der Adapter ist bewusst NICHT auf den 808S zugeschnitten.
    Jeder Sensor mit standardisiertem BLE Heart Rate Service
    sollte prinzipiell funktionieren.

    Wichtiger Betriebsgrundsatz:
    Ein nicht vorhandener Sensor ist kein fataler Fehler.

    Der Agent soll dauerhaft laufen können, auch wenn:
    - der Brustgurt gerade nicht getragen wird,
    - der Gurt außer Reichweite ist,
    - die Verbindung kurzzeitig verloren geht.
    """

    def __init__(
        self,
        device_id: str,
        discovery: BleDiscoveryCoordinator,
    ) -> None:
        self._device_id = device_id
        self._discovery = discovery

    async def _find_device(self) -> BLEDevice | None:
        return await self._discovery.find_device_by_address(
            self._device_id,
            timeout=10.0,
        )

    async def _wait_for_device(self) -> BLEDevice:
        """
        Sucht wiederholt nach einem Sensor, bis einer gefunden wird.
        """

        while True:
            device = await self._find_device()

            if device is not None:
                print(f"Heart-rate sensor found: {device.name or 'unknown'} ({device.address})")
                return device

            print(
                "No BLE heart-rate sensor found. "
                f"Retrying in {self._scan_interval_seconds:.0f} seconds ..."
            )

            await asyncio.sleep(self._scan_interval_seconds)

    def _publish_status(
        self,
        *,
        device_id: str,
        device_name: str,
        status: DeviceStatus,
    ) -> None:
        """
        Meldet den Zustand des Geräts an den Device Agent.

        Wichtig:
        Der Adapter kennt weder WebSocket noch UI noch Datenbank.

        Er veröffentlicht nur ein Domain Event.
        """

        event = DeviceStatusChanged(
            device_id=device_id,
            device_type=DeviceType.HEART_RATE,
            device_name=device_name,
            status=status,
            timestamp=datetime.now(UTC),
        )

        self._status_handler(event)

    async def samples(self) -> AsyncIterator[HeartRateSample]:
        """
        Liefert dauerhaft neue Herzfrequenzmesswerte.

        Beispiel für den Consumer:

            async for sample in source.samples():
                print(sample.bpm)

        Das ist ein asynchroner Generator.

        Java-Vergleich grob:
            Publisher<HeartRateSample>

        Bei Verbindungsverlust wird erneut nach einem Sensor gesucht.
        """

        while True:
            device = await self._wait_for_device()

            # Diese Werte werden bewusst in lokale Variablen kopiert.
            #
            # Der Callback lebt länger als ein einzelner synchroner
            # Methodenaufruf. Durch die gebundenen Werte vermeiden wir,
            # dass er später auf veränderte Loop-Variablen zugreift.
            device_id = device.address
            device_name = device.name or "unknown"

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

                    print(f"Connected to heart-rate sensor: {device_name}")

                    def notification_handler(
                        _sender: object,
                        data: bytearray,
                        *,
                        bound_device_id: str = device_id,
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
                            device_id=bound_device_id,
                            timestamp=datetime.now(UTC),
                            bpm=bpm,
                        )

                        self._queue.put_nowait(sample)

                    await client.start_notify(
                        HEART_RATE_MEASUREMENT_UUID,
                        notification_handler,
                    )

                    try:
                        while client.is_connected:
                            try:
                                # Ohne Timeout würde queue.get() unbegrenzt
                                # warten, falls die BLE-Verbindung still
                                # abbricht und keine weiteren Samples kommen.
                                sample = await asyncio.wait_for(
                                    self._queue.get(),
                                    timeout=2.0,
                                )

                                yield sample

                            except TimeoutError:
                                # Kein Sample innerhalb des Zeitfensters.
                                # Danach prüfen wir über die while-Bedingung
                                # erneut client.is_connected.
                                continue

                    finally:
                        if client.is_connected:
                            await client.stop_notify(HEART_RATE_MEASUREMENT_UUID)

            except asyncio.CancelledError:
                # Cancellation ist kein technischer BLE-Fehler.
                # Wenn der gesamte Device Agent beendet werden soll,
                # muss das Signal nach außen weitergegeben werden.
                raise

            except (BleakError, OSError, TimeoutError) as exc:
                print(
                    "Heart-rate connection lost or failed: "
                    f"{exc}. "
                    f"Retrying in "
                    f"{self._scan_interval_seconds:.0f} seconds ..."
                )

                await asyncio.sleep(self._scan_interval_seconds)

            finally:
                self._publish_status(
                    device_id=device_id,
                    device_name=device_name,
                    status=DeviceStatus.DISCONNECTED,
                )
