from datetime import UTC, datetime

from domains.health.device import Device, DeviceStatus, DeviceType
from domains.health.device_events import DeviceStatusChanged


def test_create_heart_rate_device() -> None:
    device = Device(
        id="test-device",
        type=DeviceType.HEART_RATE,
        name="808S",
    )

    assert device.type == DeviceType.HEART_RATE
    assert device.name == "808S"


def test_create_connected_event() -> None:
    event = DeviceStatusChanged(
        device_id="test-device",
        device_type=DeviceType.HEART_RATE,
        device_name="808S",
        status=DeviceStatus.CONNECTED,
        timestamp=datetime.now(UTC),
    )

    assert event.status == DeviceStatus.CONNECTED
