# WebSocket-Schnittstellen

## Überblick

Das Backend stellt drei WebSocket-Verbindungen bereit. Der lokale Device Agent liefert Telemetriedaten an das Backend. Frontend-Clients empfangen Rohtelemetrie und relevante Live-Coaching-Entscheidungen über getrennte Streams.

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
    ├──────────────► TelemetryBroadcaster ─────► /ws/telemetry
    │
    └── HeartRateSample
            │
            ▼
      Live Coaching
            │
            ▼
 LiveCoachingBroadcaster ─────────────────────► /ws/coaching
```

Die WebSocket-Schnittstellen sind nicht Bestandteil der automatisch generierten OpenAPI-Operationen. Die HTTP-Dokumentation befindet sich unter `/redoc`.

## Telemetrie-Nachrichtenformat

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
7. Gültige Herzfrequenz-Samples werden zusätzlich dem Live Coach zur Bewertung des aktiven Workouts übergeben.

### Ungültige Nachrichten

Wenn die Pydantic-Validierung fehlschlägt, wird eine Warnung protokolliert. Die Nachricht wird verworfen und die Verbindung bleibt bestehen. Es wird keine gesonderte Fehlernachricht an den Agent gesendet.

### Verbindungsende

Bei einer regulären WebSocket-Trennung wird das Ereignis protokolliert. Der Wiederverbindungsablauf des Device Agents ist nicht Teil dieses Router-Contracts.

## `/ws/telemetry`

**Richtung:** Backend → Frontend

Frontend-Clients verwenden diese Verbindung, um laufende Rohtelemetrie zu empfangen.

### Verbindungsablauf

1. Der Frontend-Client baut eine WebSocket-Verbindung auf.
2. Der TelemetryBroadcaster akzeptiert und registriert den Client.
3. Der Client empfängt JSON-Textnachrichten, die vom Device Agent verarbeitet und weitergeleitet wurden.
4. Bei einer regulären Trennung wird der Client aus dem Broadcaster entfernt.

Der Router nimmt eingehende Textnachrichten entgegen, interpretiert sie aber nicht als Steuerbefehle. Es gibt auf dieser Verbindung derzeit keinen definierten Command-Contract.

## `/ws/coaching`

**Richtung:** Backend → Frontend

Dieser Stream transportiert relevante Live-Coaching-Entscheidungen. Er ist bewusst von der Rohtelemetrie getrennt. In V1 wird ein Event nur erzeugt, wenn der Coach eine konkrete Änderung der Trainingsintensität empfiehlt. Entscheidungen mit `action = none` werden nicht übertragen.

Wiederholte identische Aktionen werden unterdrückt, solange sich die Situation nicht normalisiert oder die Coaching-Aktion wechselt. Dadurch entsteht bei dauerhaft zu hohem Puls nicht mit jedem neuen Herzfrequenz-Sample ein weiteres identisches Event.

### Eventformat

Beispiel:

```json
{
  "type": "coaching.decision",
  "timestamp": "2026-09-13T08:30:00Z",
  "workoutId": "workout-1",
  "deviceId": "heart-rate-1",
  "action": "reduce_intensity",
  "zoneStatus": "above_target",
  "heartRateBpm": 149,
  "targetMinBpm": 125,
  "targetMaxBpm": 145,
  "outsideTargetSeconds": 21.0,
  "reason": "heart_rate_above_target_long_enough"
}
```

`outsideTargetSeconds` beschreibt, wie lange die Herzfrequenz zum Entscheidungszeitpunkt bereits ununterbrochen außerhalb des Zielbereichs lag.

Der Stream enthält noch keinen ausformulierten Sprachtext. `action`, `zoneStatus` und `reason` sind fachliche Werte. Eine spätere Speech Policy kann daraus geeignete und nicht zu häufige Sprachmeldungen erzeugen.

## Broadcaster

`TelemetryBroadcaster` und `LiveCoachingBroadcaster` verwalten jeweils ihre verbundenen WebSockets. Sie kennen keine fachliche Entscheidungslogik, sondern verteilen bereits serialisierte Nachrichten an die registrierten Clients.

Wenn das Senden an einen Client mit `WebSocketDisconnect` oder `RuntimeError` fehlschlägt, wird dieser Client aus der jeweiligen Verbindungsmenge entfernt.

## Initialer Gerätezustand

Der HTTP-Endpunkt `GET /api/devices` liefert den aktuellen Zustand aller dem Backend bekannten Geräte. Er ist vom WebSocket-Stream getrennt und kann vom Frontend verwendet werden, um einen initialen Zustand oder einen erneuten Snapshot abzurufen.

Für Live-Coaching-Events gibt es derzeit bewusst kein Replay und keine Persistenz. Ein Frontend empfängt nur Events, die während seiner aktiven `/ws/coaching`-Verbindung entstehen.

## Nicht Bestandteil dieses Contracts

Die folgenden Themen werden durch diese Dokumentation nicht neu festgelegt:

* Authentifizierung oder Autorisierung der WebSocket-Verbindungen.
* Garantierte Zustellung, Nachrichtenpersistenz oder Replay.
* Ein verbindliches Heartbeat- oder Acknowledgement-Protokoll.
* Steuerbefehle vom Frontend an den Device Agent.
* Formulierung oder Sprachausgabe der Coaching-Entscheidungen.

Diese Punkte werden erst dokumentiert, wenn die entsprechende Implementierung und ihre fachlichen Regeln feststehen.
