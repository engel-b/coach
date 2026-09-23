from collections.abc import Callable
from dataclasses import replace

from features.telemetry.api.contracts.telemetry import TelemetryMessage
from features.telemetry.domain.health.device import DeviceStatus, DeviceType
from features.telemetry.domain.health.heart_rate import HeartRateSample
from features.telemetry.domain.telemetry.bike import BikeTelemetry
from features.telemetry.service.models import DeviceState

HeartRateHandler = Callable[[HeartRateSample], None]
BikeTelemetryHandler = Callable[[BikeTelemetry], None]


class TelemetryService:
    """
    Application Service für eingehende Live-Telemetrie.

    Verantwortlichkeiten:

    - TelemetryMessages entgegennehmen
    - fachlich relevante Payloads interpretieren
    - aktuellen Gerätezustand halten
    - fachliche Herzfrequenz-Samples an registrierte Interessenten weitergeben

    Nicht verantwortlich für:

    - WebSocket
    - Bluetooth
    - Datenbank
    - UI
    - Coaching-Entscheidungen
    """

    def __init__(self) -> None:
        # Key: technische Device-ID, z.B. BLE-Adresse.
        #
        # Der Dictionary-Zugriff ist für unseren kleinen lokalen
        # Mehrgerätebetrieb völlig ausreichend.
        self._devices: dict[str, DeviceState] = {}
        self._heart_rate_handlers: list[HeartRateHandler] = []
        self._bike_telemetry_handlers: list[BikeTelemetryHandler] = []

    def add_heart_rate_handler(
        self,
        handler: HeartRateHandler,
    ) -> None:
        """
        Registriert einen Interessenten für fachliche Herzfrequenz-Samples.

        Der TelemetryService kennt dabei nicht den konkreten Empfänger.
        Das kann später beispielsweise der Live Coach sein.
        """

        self._heart_rate_handlers.append(handler)

    def add_bike_telemetry_handler(
        self,
        handler: BikeTelemetryHandler,
    ) -> None:
        """Registriert einen Interessenten für normalisierte Bike-Telemetrie."""

        self._bike_telemetry_handlers.append(handler)

    def handle(self, message: TelemetryMessage) -> None:
        if message.type == "device.status_changed":
            self._handle_device_status(message)
            return

        if message.type == "heart_rate.sample":
            self._handle_heart_rate(message)
            return

        if message.type == "bike.telemetry":
            self._handle_bike_telemetry(message)
            return

        # Unbekannte Messages ignorieren wir momentan bewusst.
        #
        # Später verwenden wir dafür strukturiertes Logging.
        # Ein unbekannter Eventtyp soll aber nicht das Backend
        # zum Absturz bringen.

    def _handle_device_status(
        self,
        message: TelemetryMessage,
    ) -> None:
        """
        Aktualisiert Status-Metadaten eines Geräts.

        Bereits bekannte Telemetrie-Werte bleiben erhalten. Ein Status-Event
        beschreibt nur den Verbindungs-/Gerätezustand und darf Messwerte
        deshalb nicht überschreiben.
        """

        device_type = DeviceType(str(message.payload["deviceType"]))
        device_name = str(message.payload["deviceName"])
        status = DeviceStatus(str(message.payload["status"]))

        previous = self._devices.get(message.device_id)

        if previous is None:
            state = DeviceState(
                device_id=message.device_id,
                device_type=device_type,
                device_name=device_name,
                status=status,
                last_seen=message.timestamp,
            )
        else:
            state = replace(
                previous,
                device_type=device_type,
                device_name=device_name,
                status=status,
                last_seen=message.timestamp,
            )

        self._devices[message.device_id] = state

    def _handle_heart_rate(
        self,
        message: TelemetryMessage,
    ) -> None:
        """
        Aktualisiert den letzten bekannten Pulswert eines Geräts.
        """

        bpm_value = message.payload.get("bpm")

        if not isinstance(bpm_value, int):
            return

        previous = self._devices.get(message.device_id)

        if previous is None:
            # Normalerweise kommt vorher ein DeviceStatusChanged.
            #
            # Wir machen uns aber nicht davon abhängig.
            # Messages können bei Reconnect oder späteren Änderungen
            # auch einmal in anderer Reihenfolge eintreffen.
            state = DeviceState(
                device_id=message.device_id,
                device_type=DeviceType.HEART_RATE,
                device_name="unknown",
                status=DeviceStatus.CONNECTED,
                last_seen=message.timestamp,
                heart_rate_bpm=bpm_value,
            )
        else:
            state = replace(
                previous,
                last_seen=message.timestamp,
                heart_rate_bpm=bpm_value,
            )

        self._devices[message.device_id] = state

        sample = HeartRateSample(
            device_id=message.device_id,
            timestamp=message.timestamp,
            bpm=bpm_value,
        )

        for handler in self._heart_rate_handlers:
            handler(sample)

    def _handle_bike_telemetry(
        self,
        message: TelemetryMessage,
    ) -> None:
        """
        Aktualisiert den Device-State eines FTMS-Bikes.

        FTMS-Telemetrie kann unvollständig sein. Deshalb übernehmen wir
        bereits bekannte Werte, wenn ein Feld in der neuen Nachricht fehlt.
        """

        speed_value = message.payload.get("speedKmh")
        cadence_value = message.payload.get("cadenceRpm")
        distance_value = message.payload.get("distanceM")
        power_value = message.payload.get("powerW")
        resistance_value = message.payload.get("resistance")

        previous = self._devices.get(message.device_id)

        speed_kmh = (
            float(speed_value)
            if isinstance(speed_value, int | float)
            else previous.speed_kmh
            if previous is not None
            else None
        )

        cadence_rpm = (
            float(cadence_value)
            if isinstance(cadence_value, int | float)
            else previous.cadence_rpm
            if previous is not None
            else None
        )

        distance_m = (
            distance_value
            if isinstance(distance_value, int)
            else previous.distance_m
            if previous is not None
            else None
        )

        power_w = (
            power_value
            if isinstance(power_value, int)
            else previous.power_w
            if previous is not None
            else None
        )

        resistance = (
            resistance_value
            if isinstance(resistance_value, int)
            else previous.resistance
            if previous is not None
            else None
        )

        if previous is None:
            state = DeviceState(
                device_id=message.device_id,
                device_type=DeviceType.BIKE,
                device_name="unknown",
                status=DeviceStatus.CONNECTED,
                last_seen=message.timestamp,
                speed_kmh=speed_kmh,
                cadence_rpm=cadence_rpm,
                distance_m=distance_m,
                power_w=power_w,
                resistance=resistance,
            )
        else:
            state = replace(
                previous,
                status=DeviceStatus.CONNECTED,
                last_seen=message.timestamp,
                speed_kmh=speed_kmh,
                cadence_rpm=cadence_rpm,
                distance_m=distance_m,
                power_w=power_w,
                resistance=resistance,
            )

        self._devices[message.device_id] = state

        telemetry = BikeTelemetry(
            device_id=message.device_id,
            timestamp=message.timestamp,
            power_w=power_value if isinstance(power_value, int) else None,
            cadence_rpm=(float(cadence_value) if isinstance(cadence_value, int | float) else None),
            speed_kmh=(float(speed_value) if isinstance(speed_value, int | float) else None),
            distance_m=distance_value if isinstance(distance_value, int) else None,
            resistance=(resistance_value if isinstance(resistance_value, int) else None),
        )
        for handler in self._bike_telemetry_handlers:
            handler(telemetry)

    def get_devices(self) -> list[DeviceState]:
        """
        Liefert einen Snapshot aller aktuell bekannten Geräte.

        list(...) verhindert, dass Aufrufer unser internes Dictionary
        direkt manipulieren können.
        """

        return list(self._devices.values())

    def get_device(
        self,
        device_id: str,
    ) -> DeviceState | None:
        return self._devices.get(device_id)
