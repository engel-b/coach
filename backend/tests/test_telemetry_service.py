from datetime import UTC, datetime

from application.telemetry.service import TelemetryService
from contracts.telemetry import TelemetryMessage
from domains.health.device import DeviceStatus

DEVICE_ID = "AA:BB:CC:DD:EE:FF"


def test_device_status_is_stored() -> None:
    service = TelemetryService()

    message = TelemetryMessage(
        type="device.status_changed",
        timestamp=datetime.now(UTC),
        device_id=DEVICE_ID,
        payload={
            "deviceType": "heart_rate",
            "deviceName": "808S",
            "status": "connected",
        },
    )

    service.handle(message)

    state = service.get_device(DEVICE_ID)

    assert state is not None
    assert state.device_name == "808S"
    assert state.status == DeviceStatus.CONNECTED


def test_heart_rate_updates_device() -> None:
    service = TelemetryService()

    status_message = TelemetryMessage(
        type="device.status_changed",
        timestamp=datetime.now(UTC),
        device_id=DEVICE_ID,
        payload={
            "deviceType": "heart_rate",
            "deviceName": "808S",
            "status": "connected",
        },
    )

    service.handle(status_message)

    heart_rate_message = TelemetryMessage(
        type="heart_rate.sample",
        timestamp=datetime.now(UTC),
        device_id=DEVICE_ID,
        payload={
            "bpm": 87,
        },
    )

    service.handle(heart_rate_message)

    state = service.get_device(DEVICE_ID)

    assert state is not None
    assert state.heart_rate_bpm == 87


def test_heart_rate_without_previous_status_is_supported() -> None:
    service = TelemetryService()

    message = TelemetryMessage(
        type="heart_rate.sample",
        timestamp=datetime.now(UTC),
        device_id=DEVICE_ID,
        payload={
            "bpm": 91,
        },
    )

    service.handle(message)

    state = service.get_device(DEVICE_ID)

    assert state is not None
    assert state.heart_rate_bpm == 91
    assert state.status == DeviceStatus.CONNECTED


def test_handles_bike_telemetry() -> None:
    service = TelemetryService()

    timestamp = datetime.now(UTC)

    message = TelemetryMessage(
        type="bike.telemetry",
        timestamp=timestamp,
        device_id="test-bike",
        payload={
            "powerW": 175,
            "cadenceRpm": 82.5,
            "speedKmh": 28.4,
            "resistance": 12,
        },
    )

    service.handle(message)

    telemetry = service.get_bike_telemetry()

    assert len(telemetry) == 1

    bike = telemetry[0]

    assert bike.device_id == "test-bike"
    assert bike.timestamp == timestamp
    assert bike.power_w == 175
    assert bike.cadence_rpm == 82.5
    assert bike.speed_kmh == 28.4
    assert bike.resistance == 12


def test_handles_partial_bike_telemetry() -> None:
    service = TelemetryService()

    message = TelemetryMessage(
        type="bike.telemetry",
        timestamp=datetime.now(UTC),
        device_id="test-bike",
        payload={
            "cadenceRpm": 75,
        },
    )

    service.handle(message)

    bike = service.get_bike_telemetry()[0]

    assert bike.power_w is None
    assert bike.cadence_rpm == 75.0
    assert bike.speed_kmh is None
    assert bike.resistance is None
