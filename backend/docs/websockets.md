# WebSocket-Schnittstellen

## Überblick

Das Backend stellt zwei WebSocket-Verbindungen bereit. Der lokale Device Agent liefert Telemetriedaten an das Backend. Frontend-Clients empfangen die verarbeiteten Meldungen über eine separate Verbindung.

```text
Device Agent
    │
    │ JSON-Textnachrichten
    ▼
/ws/device-agent
    │
    ▼
TelemetryService
    │
    ▼
TelemetryBroadcaster
    │
    ├──► Frontend-Client 1
    ├──► Frontend-Client 2
    └──► Frontend-Client n
```

Die WebSocket-Schnittstellen sind nicht Bestandteil der automatisch generierten OpenAPI-Operationen. Die HTTP-Dokumentation befindet sich unter `/redoc`.

## Gemeinsames Nachrichtenformat

Die Nachrichten zwischen Device Agent und Backend verwenden den Pydantic-Contract `TelemetryMessage` aus `contracts/telemetry.py`.

| JSON-Feld   | Typ      | Bedeutung                                     |
| ----------- | -------- | --------------------------------------------- |
| `type`      | string   | Nachrichtentyp für die fachliche Verarbeitung |
| `timestamp` | datetime | Zeitpunkt der Meldung                         |
| `deviceId`  | string   | Kennung des betroffenen Geräts                |
| `payload`   | object   | Nachrichtentypspezifische Daten               |

Python-intern werden Feldnamen wie `device_id` verwendet. Die JSON-Schnittstelle verwendet camelCase. Die Umwandlung erfolgt über den Pydantic-Alias-Generator.

Der Payload ist derzeit ein allgemeines Dictionary. Die unterstützten Nachrichtentypen und ihre konkreten Felder werden durch die Geräteadapter und den TelemetryService bestimmt. Dieser Transport-Contract definiert noch keine geschlossene Liste von Event-Typen.

## `/ws/device-agent`

**Richtung:** Device Agent → Backend

Diese Verbindung dient zur Übertragung von Gerätestatus und Telemetrie an das Backend.

### Verbindungsablauf

1. Der Device Agent baut eine WebSocket-Verbindung auf.
2. Das Backend akzeptiert die Verbindung.
3. Der Agent sendet JSON-Textnachrichten.
4. Das Backend validiert jede Nachricht mit `TelemetryMessage.model_validate_json`.
5. Gültige Nachrichten werden an den TelemetryService übergeben.
6. Anschließend wird die Nachricht mit camelCase-Aliasen serialisiert und an die Frontend-Clients verteilt.

### Ungültige Nachrichten

Wenn die Pydantic-Validierung fehlschlägt, wird eine Warnung protokolliert. Die Nachricht wird verworfen und die Verbindung bleibt bestehen. Es wird keine gesonderte Fehlernachricht an den Agent gesendet.

### Verbindungsende

Bei einer regulären WebSocket-Trennung wird das Ereignis protokolliert. Der Wiederverbindungsablauf des Device Agents ist nicht Teil dieses Router-Contracts.

## `/ws/telemetry`

**Richtung:** Backend → Frontend

Frontend-Clients verwenden diese Verbindung, um laufende Telemetriemeldungen zu empfangen.

### Verbindungsablauf

1. Der Frontend-Client baut eine WebSocket-Verbindung auf.
2. Der TelemetryBroadcaster akzeptiert und registriert den Client.
3. Der Client empfängt JSON-Textnachrichten, die vom Device Agent verarbeitet und weitergeleitet wurden.
4. Bei einer regulären Trennung wird der Client aus dem Broadcaster entfernt.

Der Router nimmt eingehende Textnachrichten entgegen, interpretiert sie aber nicht als Steuerbefehle. Es gibt auf dieser Verbindung derzeit keinen definierten Command-Contract.

## TelemetryBroadcaster

Der Broadcaster verwaltet eine Menge verbundener WebSockets. Er kennt weder Gerätetypen noch fachliche Messwerte. Eine Nachricht wird als String an alle registrierten Clients gesendet.

Wenn das Senden an einen Client mit `WebSocketDisconnect` oder `RuntimeError` fehlschlägt, wird dieser Client aus der Verbindungsmenge entfernt.

## Initialer Gerätezustand

Der HTTP-Endpunkt `GET /api/devices` liefert den aktuellen Zustand aller dem Backend bekannten Geräte. Er ist vom WebSocket-Stream getrennt und kann vom Frontend verwendet werden, um einen initialen Zustand oder einen erneuten Snapshot abzurufen.

## Nicht Bestandteil dieses Contracts

Die folgenden Themen werden durch diese Dokumentation nicht neu festgelegt:

* Konkrete Payload-Schemas einzelner Nachrichtentypen.
* Authentifizierung oder Autorisierung der WebSocket-Verbindungen.
* Garantierte Zustellung, Nachrichtenpersistenz oder Replay.
* Ein verbindliches Heartbeat- oder Acknowledgement-Protokoll.
* Steuerbefehle vom Frontend an den Device Agent.

Diese Punkte werden erst dokumentiert, wenn die entsprechende Implementierung und ihre fachlichen Regeln feststehen.
