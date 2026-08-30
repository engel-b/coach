from dataclasses import replace

from application.telemetry.models import DeviceState
from contracts.telemetry import TelemetryMessage
from domains.health.device import DeviceStatus, DeviceType
from domains.telemetry.bike import BikeTelemetry


class TelemetryService:
    """
    Application Service für eingehende Live-Telemetrie.

    Verantwortlichkeiten:

    - TelemetryMessages entgegennehmen
    - fachlich relevante Payloads interpretieren
    - aktuellen Gerätezustand halten

    Nicht verantwortlich für:

    - WebSocket
    - Bluetooth
    - Datenbank
    - UI

    Java-/Spring-Vergleich:

        @Service
        public class TelemetryService {
            ...
        }

    Nur ohne Framework-Annotation.
    """

    def __init__(self) -> None:
        # Key: technische Device-ID, z.B. BLE-Adresse.
        #
        # Der Dictionary-Zugriff ist für unseren kleinen lokalen
        # Mehrgerätebetrieb völlig ausreichend.
        self._devices: dict[str, DeviceState] = {}
        self._bike_telemetry: dict[
            str,
            BikeTelemetry,
        ] = {}

    def handle(self, message: TelemetryMessage) -> None:
        """
        Zentraler Einstiegspunkt für Telemetrie vom Device Agent.

        Später können hier weitere Nachrichtentypen ergänzt werden:

            bike.telemetry
            scale.measurement
            device.status_changed
            ...
        """

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
        Verarbeitet beispielsweise:

        {
            "type": "device.status_changed",
            "deviceId": "...",
            "payload": {
                "deviceType": "heart_rate",
                "deviceName": "808S",
                "status": "connected"
            }
        }
        """

        device_type_value = message.payload.get("deviceType")
        device_name_value = message.payload.get("deviceName")
        status_value = message.payload.get("status")

        # Payload kommt von einer Prozessgrenze.
        #
        # Wir verlassen uns deshalb nicht blind darauf,
        # dass die Typen korrekt sind.
        if not isinstance(device_type_value, str):
            return

        if not isinstance(device_name_value, str):
            return

        if not isinstance(status_value, str):
            return

        try:
            device_type = DeviceType(device_type_value)
            status = DeviceStatus(status_value)
        except ValueError:
            # Unbekannter Enum-Wert.
            return

        previous = self._devices.get(message.device_id)

        state = DeviceState(
            device_id=message.device_id,
            device_type=device_type,
            device_name=device_name_value,
            status=status,
            last_seen=message.timestamp,
            heart_rate_bpm=(previous.heart_rate_bpm if previous is not None else None),
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
            # dataclasses.replace ist bei frozen dataclasses sehr praktisch.
            #
            # Java-Vergleich:
            # Wir erzeugen einen neuen Record mit geänderten Feldern.
            state = replace(
                previous,
                last_seen=message.timestamp,
                heart_rate_bpm=bpm_value,
            )

        self._devices[message.device_id] = state

    def _handle_bike_telemetry(
        self,
        message: TelemetryMessage,
    ) -> None:
        """
        Aktualisiert den letzten bekannten Telemetrie-Snapshot
        eines Fahrrads.

        Fehlende Werte bleiben None. Dadurch unterscheiden wir
        sauber zwischen "nicht geliefert" und einem echten Wert 0.
        """

        power_w = message.payload.get("powerW")
        cadence_rpm = message.payload.get("cadenceRpm")
        speed_kmh = message.payload.get("speedKmh")
        resistance = message.payload.get("resistance")

        if power_w is not None and not isinstance(
            power_w,
            int,
        ):
            return

        if cadence_rpm is not None and not isinstance(
            cadence_rpm,
            (int, float),
        ):
            return

        if speed_kmh is not None and not isinstance(
            speed_kmh,
            (int, float),
        ):
            return

        if resistance is not None and not isinstance(
            resistance,
            int,
        ):
            return

        telemetry = BikeTelemetry(
            device_id=message.device_id,
            timestamp=message.timestamp,
            power_w=power_w,
            cadence_rpm=(float(cadence_rpm) if cadence_rpm is not None else None),
            speed_kmh=(float(speed_kmh) if speed_kmh is not None else None),
            resistance=resistance,
        )

        self._bike_telemetry[message.device_id] = telemetry

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

    def get_bike_telemetry(
        self,
    ) -> list[BikeTelemetry]:
        """
        Liefert den letzten bekannten Snapshot
        aller Fahrräder.
        """

        return list(self._bike_telemetry.values())
