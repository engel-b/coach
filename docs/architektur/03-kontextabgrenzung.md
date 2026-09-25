# 3. Kontextabgrenzung

## 3.1 Fachlicher Kontext

```text
                         +----------------------+
                         | Trainierende Person  |
                         +----------+-----------+
                                    |
                         Maus / Anzeige / Sprache
                                    v
+------------------+       +--------+---------+       +------------------+
| Bluetooth-       | ----> | Digital Fitness  | ----> | Workout-Video /  |
| Geräte/Sensoren  |       | Coach             |       | Trainingsmedien  |
+------------------+       +--------+---------+       +------------------+
                                    |
                                    v
                         +----------+-----------+
                         | SQLite DB            |
                         | Profile / Check-ins  |
                         | Workouts / Phasen    |
                         +----------------------+
```

## 3.2 Technischer Kontext

```text
+------------------------- Browser / Kiosk ---------------------------+
| React / TypeScript                                                   |
|                                                                      |
| Dashboard     Workout UI      Telemetry UI      Coach UI / Audio     |
+-----+--------------+---------------+--------------------+-------------+
      | HTTP         | HTTP          | WS /telemetry      | WS /coaching
      +--------------+---------------+--------------------+
                                     v
+------------------------------ FastAPI API ---------------------------+
| Composition Root / Wiring                                            |
|                                                                      |
| Person  CheckIn  Training  Workout  Telemetry  Coaching  Speech      |
+---+--------+---------+--------+----------+----------+--------+--------+
    |        |         |        |          |          |        |
    |        |         |        |          |          |        +--> Piper
    |        |         |        |          |          |
    |        |         |        |          |          +--> Local LLM [optional]
    |        |         |        |          |
    +--------+---------+--------+----------+--------------> SQLite
                                         |
                                         v
                              +----------+-----------+
                              | Device Agent         |
                              | Bluetooth Adapter    |
                              +-----+-----------+----+
                                    |           |
                                   FTMS         HR
```

### Systemgrenzen

Das Frontend analysiert keine Rohtelemetrie, um selbst Coaching-Entscheidungen zu treffen. Rohdaten und fachliche Coaching-Events haben deshalb getrennte Streams:

```text
/ws/telemetry
    -> Geräte-/Messdaten

/ws/coaching
    -> fachlich relevante Coach-Ereignisse
```

---


## 3.3 Externe technische Schnittstellen

| Schnittstelle | Richtung | Protokoll | Zweck |
|---|---|---|---|
| Browser ↔ API | bidirektional | HTTP/JSON | Personen, Check-ins, Empfehlungen, Workouts, Videos, Verwaltung |
| Browser ↔ API | bidirektional | WebSocket | Live-Telemetrie und fachliche Coaching-Ereignisse |
| Browser → Caddy/FastAPI | lesend | HTTP | statische Trainingsvideos unter `/videos/*` |
| Device Agent ↔ API | bidirektional | WebSocket | Telemetrie und Gerätezustände |
| Device Agent ↔ HR-Sensor | bidirektional | BLE/GATT | Heart-Rate-Messwerte |
| Device Agent ↔ Bike | bidirektional | BLE/GATT/FTMS | Bike-Telemetrie; aktive Steuerung separat/später |
| Backend ↔ SQLite | bidirektional | SQL/Dateizugriff | lokale Persistenz |
| Backend → Piper | lokal | Prozess/Library-Adapter | Text-to-Speech |
| Backend → llama-server | lokal | HTTP/OpenAI-kompatibel | optionale Coach-Formulierung |

Die API und `llama-server` lauschen im Produktivbetrieb nur auf Loopback. Caddy bildet die HTTP-Einstiegsgrenze für den Browser.

---
