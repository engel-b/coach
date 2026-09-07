from datetime import UTC, datetime

from domains.telemetry.bike import BikeTelemetry


def test_bike_telemetry_can_contain_all_measurements() -> None:
    timestamp = datetime.now(UTC)

    telemetry = BikeTelemetry(
        device_id="test-bike",
        timestamp=timestamp,
        power_w=175,
        cadence_rpm=82.5,
        speed_kmh=28.4,
        resistance=12,
    )

    assert telemetry.device_id == "test-bike"
    assert telemetry.timestamp == timestamp
    assert telemetry.power_w == 175
    assert telemetry.cadence_rpm == 82.5
    assert telemetry.speed_kmh == 28.4
    assert telemetry.resistance == 12


def test_bike_telemetry_allows_missing_measurements() -> None:
    telemetry = BikeTelemetry(
        device_id="test-bike",
        timestamp=datetime.now(UTC),
        cadence_rpm=75.0,
    )

    assert telemetry.power_w is None
    assert telemetry.cadence_rpm == 75.0
    assert telemetry.speed_kmh is None
    assert telemetry.resistance is None
