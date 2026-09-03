import asyncio
from collections.abc import Callable
from typing import Self

import pytest
from bleak.exc import BleakError

from adapters.bluetooth.discovery import BleDiscoveryCoordinator
from adapters.bluetooth.ftms import adapter
from adapters.bluetooth.ftms.adapter import (
    FTMS_INDOOR_BIKE_DATA_UUID,
    FtmsBikeAdapter,
)


class FakeBleakClient:
    """
    Minimaler BleakClient-Ersatz für Adapter-Tests.

    Wir testen hier bewusst nicht Bleak selbst, sondern nur unser Verhalten:
    - Verbindung wird aufgebaut
    - Notifications werden aktiviert
    - bei ausbleibender Telemetrie entsteht ein BleakError
    - Notifications werden anschließend wieder beendet

    Java-Vergleich:
    ungefähr ein kleiner Fake für einen Infrastructure Client.
    """

    last_instance: "FakeBleakClient | None" = None

    def __init__(self, device: object) -> None:
        self.device = device
        self.is_connected = True
        self.notification_handler: Callable[[object, bytearray], None] | None = None
        self.stop_notify_called = False

        FakeBleakClient.last_instance = self

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: object,
        exc: object,
        traceback: object,
    ) -> None:
        self.is_connected = False

    async def start_notify(
        self,
        characteristic: str,
        handler: Callable[[object, bytearray], None],
    ) -> None:
        assert characteristic == FTMS_INDOOR_BIKE_DATA_UUID
        self.notification_handler = handler

    async def stop_notify(self, characteristic: str) -> None:
        assert characteristic == FTMS_INDOOR_BIKE_DATA_UUID
        self.stop_notify_called = True


@pytest.mark.asyncio
async def test_telemetry_raises_when_connected_bike_stays_silent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    Eine technisch bestehende BLE-Verbindung reicht nicht aus.

    Wenn keine FTMS Notifications eintreffen, muss der Adapter den
    Verbindungs-Lifecycle mit BleakError beenden. Der Device-Worker kann
    anschließend einen Reconnect durchführen.
    """

    bike_adapter = FtmsBikeAdapter(
        device_id="24:00:0C:A0:9A:95",
        discovery=BleDiscoveryCoordinator(),
        telemetry_timeout_seconds=0.01,
    )

    async def fake_find_device() -> object:
        return object()

    monkeypatch.setattr(
        bike_adapter,
        "_find_device",
        fake_find_device,
    )

    monkeypatch.setattr(
        adapter,
        "BleakClient",
        FakeBleakClient,
    )

    telemetry = bike_adapter.telemetry()

    with pytest.raises(
        BleakError,
        match="telemetry became silent",
    ):
        await anext(telemetry)

    client = FakeBleakClient.last_instance

    assert client is not None
    assert client.stop_notify_called is True


@pytest.mark.asyncio
async def test_telemetry_raises_when_bike_becomes_silent_after_first_sample(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    Auch eine zunächst funktionierende Verbindung darf später nicht
    unbegrenzt auf queue.get() hängen.

    Nach einem gültigen Sample muss derselbe Silence-Timeout weiterhin
    aktiv sein.
    """

    bike_adapter = FtmsBikeAdapter(
        device_id="24:00:0C:A0:9A:95",
        discovery=BleDiscoveryCoordinator(),
        telemetry_timeout_seconds=0.01,
    )

    async def fake_find_device() -> object:
        return object()

    monkeypatch.setattr(
        bike_adapter,
        "_find_device",
        fake_find_device,
    )

    monkeypatch.setattr(
        adapter,
        "BleakClient",
        FakeBleakClient,
    )

    telemetry = bike_adapter.telemetry()

    first_sample_task = asyncio.create_task(
        anext(telemetry),
    )

    # Dem Generator kurz Zeit geben, BleakClient.start_notify()
    # aufzurufen und den Callback im Fake zu registrieren.
    await asyncio.sleep(0)

    client = FakeBleakClient.last_instance

    assert client is not None
    assert client.notification_handler is not None

    # Gültiges FTMS Indoor Bike Data.
    #
    # Flags = 0, anschließend Instantaneous Speed = 2500.
    # FTMS kodiert Speed in 0,01 km/h -> 25,00 km/h.
    client.notification_handler(
        object(),
        bytearray(
            [
                0x00,
                0x00,
                0xC4,
                0x09,
            ]
        ),
    )

    first_sample = await first_sample_task

    assert first_sample.speed_kmh == 25.0

    # Danach kommt keine weitere Notification.
    # Der zweite anext()-Aufruf muss deshalb über unseren Timeout
    # mit BleakError enden.
    with pytest.raises(
        BleakError,
        match="telemetry became silent",
    ):
        await anext(telemetry)

    assert client.stop_notify_called is True
