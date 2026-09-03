from datetime import UTC, datetime, timedelta

from application.telemetry.service import TelemetryService
from contracts.telemetry import TelemetryMessage
from domains.health.device import DeviceStatus, DeviceType

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

    bike = service.get_device("test-bike")

    assert bike is not None
    assert bike.device_type == DeviceType.BIKE
    assert bike.status == DeviceStatus.CONNECTED
    assert bike.last_seen == timestamp
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

    bike = service.get_device("test-bike")

    assert bike is not None
    assert bike.device_type == DeviceType.BIKE
    assert bike.status == DeviceStatus.CONNECTED
    assert bike.cadence_rpm == 75.0
    assert bike.speed_kmh is None
    assert bike.power_w is None
    assert bike.resistance is None


def test_bike_telemetry_creates_device_state() -> None:
    """
    Bike-Telemetrie allein reicht aus, um das Bike als bekanntes
    und verbundenes Gerät im Device-State anzulegen.

    Damit hängt der Device-Snapshot nicht davon ab, dass vorher
    zwingend ein separates device.status_changed eingetroffen ist.
    """

    service = TelemetryService()

    timestamp = datetime.now(UTC)

    message = TelemetryMessage(
        type="bike.telemetry",
        timestamp=timestamp,
        device_id="24:00:0C:A0:9A:95",
        payload={
            "speedKmh": 25.4,
            "cadenceRpm": 82.0,
            "powerW": 175,
            "resistance": 12,
        },
    )

    service.handle(message)

    device = service.get_device(
        "24:00:0C:A0:9A:95",
    )

    assert device is not None
    assert device.device_id == "24:00:0C:A0:9A:95"
    assert device.device_type == DeviceType.BIKE
    assert device.status == DeviceStatus.CONNECTED
    assert device.last_seen == timestamp
    assert device.speed_kmh == 25.4
    assert device.cadence_rpm == 82.0
    assert device.power_w == 175
    assert device.resistance == 12


def test_partial_bike_telemetry_preserves_previous_values() -> None:
    """
    FTMS-Nachrichten können nur einen Teil der möglichen Messwerte
    enthalten.

    Fehlende Werte dürfen deshalb einen bereits bekannten Wert nicht
    versehentlich wieder auf None setzen.
    """

    service = TelemetryService()

    first_timestamp = datetime.now(UTC)
    second_timestamp = first_timestamp + timedelta(seconds=1)

    service.handle(
        TelemetryMessage(
            type="bike.telemetry",
            timestamp=first_timestamp,
            device_id="24:00:0C:A0:9A:95",
            payload={
                "speedKmh": 25.4,
                "cadenceRpm": 82.0,
                "powerW": 175,
                "resistance": 12,
            },
        )
    )

    service.handle(
        TelemetryMessage(
            type="bike.telemetry",
            timestamp=second_timestamp,
            device_id="24:00:0C:A0:9A:95",
            payload={
                "powerW": 190,
            },
        )
    )

    device = service.get_device(
        "24:00:0C:A0:9A:95",
    )

    assert device is not None
    assert device.last_seen == second_timestamp

    assert device.speed_kmh == 25.4
    assert device.cadence_rpm == 82.0
    assert device.power_w == 190
    assert device.resistance == 12


def test_device_status_preserves_existing_bike_telemetry() -> None:
    """
    Ein späteres Status-Event darf bereits bekannte Bike-Messwerte
    nicht aus dem Device-State entfernen.

    Status und Messwerte beschreiben unterschiedliche Aspekte desselben
    Gerätezustands und müssen deshalb zusammengeführt werden.
    """

    service = TelemetryService()

    telemetry_timestamp = datetime.now(UTC)
    status_timestamp = telemetry_timestamp + timedelta(seconds=1)

    service.handle(
        TelemetryMessage(
            type="bike.telemetry",
            timestamp=telemetry_timestamp,
            device_id="test-bike",
            payload={
                "speedKmh": 28.4,
                "cadenceRpm": 82.5,
                "powerW": 175,
                "resistance": 12,
            },
        )
    )

    service.handle(
        TelemetryMessage(
            type="device.status_changed",
            timestamp=status_timestamp,
            device_id="test-bike",
            payload={
                "deviceType": "bike",
                "deviceName": "MERACH",
                "status": "connected",
            },
        )
    )

    bike = service.get_device("test-bike")

    assert bike is not None

    assert bike.device_type == DeviceType.BIKE
    assert bike.device_name == "MERACH"
    assert bike.status == DeviceStatus.CONNECTED
    assert bike.last_seen == status_timestamp

    assert bike.speed_kmh == 28.4
    assert bike.cadence_rpm == 82.5
    assert bike.power_w == 175
    assert bike.resistance == 12


def test_heart_rate_sample_creates_device_state() -> None:
    """
    Ein Heart-Rate-Sample allein reicht aus, um einen Device-State
    für den Sensor anzulegen.

    Damit hängt die Sichtbarkeit des Sensors nicht davon ab, dass vorher
    zwingend ein separates device.status_changed eingetroffen ist.
    """

    service = TelemetryService()

    timestamp = datetime.now(UTC)

    service.handle(
        TelemetryMessage(
            type="heart_rate.sample",
            timestamp=timestamp,
            device_id="test-heart-rate",
            payload={
                "bpm": 142,
            },
        )
    )

    device = service.get_device("test-heart-rate")

    assert device is not None
    assert device.device_id == "test-heart-rate"
    assert device.device_type == DeviceType.HEART_RATE
    assert device.status == DeviceStatus.CONNECTED
    assert device.last_seen == timestamp
    assert device.heart_rate_bpm == 142


def test_device_status_preserves_existing_heart_rate() -> None:
    """
    Ein späteres Status-Event darf den zuletzt bekannten Puls
    nicht aus dem Device-State entfernen.
    """

    service = TelemetryService()

    sample_timestamp = datetime.now(UTC)
    status_timestamp = sample_timestamp + timedelta(seconds=1)

    service.handle(
        TelemetryMessage(
            type="heart_rate.sample",
            timestamp=sample_timestamp,
            device_id="test-heart-rate",
            payload={
                "bpm": 142,
            },
        )
    )

    service.handle(
        TelemetryMessage(
            type="device.status_changed",
            timestamp=status_timestamp,
            device_id="test-heart-rate",
            payload={
                "deviceType": "heart_rate",
                "deviceName": "808S",
                "status": "connected",
            },
        )
    )

    device = service.get_device("test-heart-rate")

    assert device is not None
    assert device.device_type == DeviceType.HEART_RATE
    assert device.device_name == "808S"
    assert device.status == DeviceStatus.CONNECTED
    assert device.last_seen == status_timestamp
    assert device.heart_rate_bpm == 142
