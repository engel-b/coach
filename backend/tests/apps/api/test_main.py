from fastapi.testclient import TestClient

from apps.api.main import app

client = TestClient(app)


def test_get_devices_returns_camel_case_api_contract() -> None:
    """
    Ein Gerätestatus und anschließend Telemetrie kommen über
    dieselbe öffentliche WebSocket-Grenze herein wie im echten Betrieb.

    Anschließend prüfen wir den REST-Vertrag von /api/devices.

    Wichtig:
    Intern darf Python weiterhin snake_case verwenden.
    Auf der HTTP-Grenze erwarten wir camelCase.
    """

    device_id = "api-contract-test-bike"

    with client.websocket_connect(
        "/ws/device-agent",
    ) as websocket:
        websocket.send_json(
            {
                "type": "device.status_changed",
                "timestamp": "2026-09-03T08:59:59Z",
                "deviceId": device_id,
                "payload": {
                    "deviceType": "bike",
                    "deviceName": "FTMS Bike",
                    "status": "connected",
                },
            },
        )

        websocket.send_json(
            {
                "type": "bike.telemetry",
                "timestamp": "2026-09-03T09:00:00Z",
                "deviceId": device_id,
                "payload": {
                    "speedKmh": 28.4,
                    "cadenceRpm": 82.5,
                    "distanceM": 1234,
                    "powerW": 175,
                    "resistance": 12,
                },
            },
        )

    response = client.get("/api/devices")

    assert response.status_code == 200

    body = response.json()

    assert isinstance(body, list)

    device = next(item for item in body if item["deviceId"] == device_id)

    assert device == {
        "deviceId": device_id,
        "deviceType": "bike",
        "deviceName": "FTMS Bike",
        "status": "connected",
        "lastSeen": "2026-09-03T09:00:00Z",
        "heartRateBpm": None,
        "speedKmh": 28.4,
        "cadenceRpm": 82.5,
        "distanceM": 1234,
        "powerW": 175,
        "resistance": 12,
    }


def test_get_devices_does_not_expose_snake_case_fields() -> None:
    """
    Dieser Test schützt speziell die Architekturgrenze.

    Ein versehentliches asdict(DeviceState) würde wieder
    snake_case nach außen geben und soll deshalb auffallen.
    """

    device_id = "api-contract-snake-case-test"

    with client.websocket_connect(
        "/ws/device-agent",
    ) as websocket:
        websocket.send_json(
            {
                "type": "heart_rate.sample",
                "timestamp": "2026-09-03T09:01:00Z",
                "deviceId": device_id,
                "payload": {
                    "bpm": 142,
                },
            },
        )

    response = client.get("/api/devices")

    assert response.status_code == 200

    body = response.json()

    device = next(item for item in body if item["deviceId"] == device_id)

    assert "deviceId" in device
    assert "deviceType" in device
    assert "deviceName" in device
    assert "lastSeen" in device
    assert "heartRateBpm" in device
    assert "distanceM" in device

    assert "device_id" not in device
    assert "device_type" not in device
    assert "device_name" not in device
    assert "last_seen" not in device
    assert "heart_rate_bpm" not in device
    assert "distance_m" not in device
