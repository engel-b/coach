# Digital Fitness Coach – Architektur- und Entwicklerdokumentation

> **Kanonische Dokumentation**  
> Stand: 19. September 2026  
> Diese Datei ersetzt die früheren Varianten `arc42-digital-fitness-coach.md`, `arc42-digital-fitness-coach-aktuell.md`, `arc42-digital-fitness-coach-mit-llm-plan.md` und `arc42-digital-fitness-coach-tts-aktualisiert.md` als zentrale Referenz.
>
> Sie beschreibt den **implementierten Stand**, ausdrücklich gekennzeichnete **optionale/experimentelle Bausteine** sowie die **geplante Weiterentwicklung**. Deployment-Details werden ergänzend in `DEPLOYMENT.md` gepflegt.

---

## Dokumentstatus auf einen Blick

| Bereich | Status | Aktueller Stand |
|---|---|---|
| Personen / Profile | ✅ Vorhanden | Mehrpersonenbetrieb, Profil, Trainingsziel, Start-/Zielgewicht, optionale maximale HF |
| Check-in | ✅ Vorhanden | Energie, Erholung, Muskelkater, Stress, verfügbare Zeit, Gewicht, Schlaf, Schritte, Historie |
| Trainingsempfehlung | ✅ Vorhanden | deterministischer Pre-Workout-Planner mit Readiness, Gewichtstrend und Gewichtsfortschritt |
| Workout | ✅ Vorhanden | Phasen, Runtime-State, Pause, Finish-Window, Overtime, Persistenz und Summary |
| Telemetrie | ✅ Vorhanden | FTMS + Heart Rate über separaten Device Agent; Sensorik optional |
| Live-Coaching | ✅ Vorhanden | HR-Abweichung, Pause/Resume, Phasenwechsel, Phasenende, Halbzeit, WebSocket-Events |
| TTS | ✅ Vorhanden | lokale Piper-Synthese hinter Port/Adapter; konfigurierbares Coach-Preset |
| Coach-Avatar | ✅ Vorhanden | wiederverwendbarer Avatar im Dashboard und Workout-Frontend |
| Lokales LLM | 🧪 Optional / experimentell | lokaler OpenAI-kompatibler Adapter mit Timeout und deterministischem Fallback |
| Appliance-Deployment | ✅ Vorhanden / im Ausbau | Debian, systemd, `provision.sh`, `prepare.sh`, API/Device-Agent/LLM als Services |
| Adaptive Workout-Anpassung | 🧭 Geplant | deterministische Adjustment-/Safety-Policy vor automatischer Änderung |
| Spracheingabe | 🧭 Geplant | Sprache als zusätzlicher Interaktionskanal, nicht als einziger Bedienpfad |

---

# 1. Einführung und Ziele

Der **Digital Fitness Coach** ist eine lokal betriebene Fitness- und Gesundheitsanwendung für mehrere Personen. Sie verbindet persönliche Profile, tägliche Check-ins, Gesundheitswerte, Trainingsempfehlungen, Workout-Durchführung, Bluetooth-Sensorik, Live-Coaching, Sprachausgabe und Fortschrittsdarstellung.

Das System soll nicht nur Messwerte anzeigen, sondern auf Basis von **Profil, Tagesform, Trainingshistorie, Workout-Phase und Live-Telemetrie** nachvollziehbar reagieren. Dabei gilt als wichtigstes Architekturprinzip:

```text
Deterministische Fachlogik entscheidet, WAS gilt und WAS passieren darf.
Optionale generative Komponenten dürfen höchstens beeinflussen, WIE etwas formuliert wird.
```

Das gilt insbesondere für Trainingsbelastung, Safety-Grenzen, Gewichtsinterpretation und Live-Coaching.

Die Anwendung ist als **lokale Appliance/Kiosk-Lösung** ausgelegt. Kernfunktionen sollen ohne Cloud-Abhängigkeit funktionieren. Optionale Komponenten wie HR-Sensor, TTS oder lokales LLM dürfen den Workout-Kern nicht unnötig blockieren.

## 1.1 Qualitätsziele

| Priorität | Ziel | Konsequenz |
|---:|---|---|
| 1 | Zuverlässigkeit | Datenintegrität, reproduzierbarer Start, saubere Migrationen, robuste Fallbacks |
| 2 | Nachvollziehbare Coaching-Logik | deterministische, testbare Regeln und explizite Gründe |
| 3 | Wartbarkeit | Package-by-Feature, klare Ports/Adapter, kleine Verantwortlichkeiten |
| 4 | Lokaler Betrieb | Kernfunktionen offline und ohne Cloud-Abhängigkeit |
| 5 | Bedienbarkeit | große klare UI, Coach-Feedback sichtbar und hörbar, Maus als vollständiger Bedienpfad |
| 6 | Erweiterbarkeit | LLM, TTS, Sensorik und weitere Coaching-Signale austauschbar ergänzbar |
| 7 | Verständlichkeit | Architekturdiagramme, ADRs, explizite Verträge und konsistente Entwicklerdokumentation |

## 1.2 Nicht-Ziele und Grenzen

Der Coach ist **kein medizinisches Diagnosesystem**. Er darf Trainings- und Gesundheitsdaten für Fitness-Coaching verwenden, soll aber keine Diagnosen oder unbelegten medizinischen Ursachen behaupten.

Gewichtsverlauf und Zielgewicht werden beschreibend ausgewertet. Ohne explizit konfigurierte Ziel-Abnahmerate wird aus einem langsameren oder schnelleren Gewichtsverlauf **keine automatische Intensivierung des Trainings** abgeleitet.

---

# 2. Randbedingungen

## 2.1 Technischer Stack

- Backend: Python, FastAPI, Pydantic, SQLAlchemy, Alembic
- Persistenz: SQLite
- Frontend: React + TypeScript + Vite
- Tests: pytest / mypy / Ruff im Backend, Vitest / ESLint im Frontend
- Device Agent: separater Python-Prozess
- Bluetooth: FTMS und Heart Rate
- TTS: lokale Piper-Engine, Browser-Speech höchstens als Fallback
- Lokales LLM: OpenAI-kompatible HTTP-Schnittstelle, aktuell über `llama-server`
- Produktion: Debian + systemd
- Entwicklung: Windows und Linux

## 2.2 Betriebsrandbedingungen

Zielhardware der aktuellen Appliance ist ein Lenovo ThinkCentre M900z mit Intel Core i3-6100 und 16 GB RAM. Eine dedizierte GPU wird weder für den Kernbetrieb noch für TTS vorausgesetzt.

Die produktiven Prozesse laufen getrennt:

```text
health-coach-prepare.service
health-coach-api.service
health-coach-device-agent.service
health-coach-llm.service       [optional]
Frontend-Service               [separat]
```

## 2.3 Fachliche Randbedingungen

- optionale Gesundheitswerte bleiben `null`, wenn unbekannt;
- ein fehlender HR-Sensor verhindert kein Workout;
- Coaching-Entscheidungen werden serverseitig erzeugt;
- Workout-Status wird serverseitig final bestimmt;
- Browser und Backend kommunizieren über explizite HTTP-/WebSocket-Verträge;
- LLM und TTS sind austauschbare technische Komponenten und keine fachlichen Entscheidungsträger.

---

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

# 4. Lösungsstrategie

1. **Package-by-Feature** statt einer globalen Schichtenstruktur.
2. Domänenmodelle bleiben frei von Infrastrukturwissen.
3. `service/` enthält Use Cases und Anwendungslogik.
4. API-Verträge sind von Domänenobjekten getrennt.
5. Persistenz läuft über Repository-Abstraktionen und SQLAlchemy-Adapter.
6. Cross-Feature-Orchestrierung liegt im App-/Composition-Root, nicht in den Features selbst.
7. Sensorik ist optional und darf den Workout-Lebenszyklus nicht blockieren.
8. Coaching-Entscheidungen werden zuerst deterministisch getroffen.
9. Entscheidung, Formulierung, Speech Policy und Audioerzeugung sind getrennte Verantwortlichkeiten.
10. Ein lokales LLM ist optional und erhält nur explizit ausgewählte Coaching-Fakten.
11. Ein LLM-Ausfall führt zum deterministischen Fallback, nicht zum Ausfall der Anwendung.
12. Lokale TTS wird über einen Port gekapselt; Piper ist die aktuelle Implementierung.
13. Deployment und Boot-Vorbereitung sind getrennt: `provision.sh` vs. `prepare.sh`.
14. Änderungen werden in kleinen, testbaren Schritten umgesetzt.

---

# 5. Bausteinsicht

## 5.1 Backend-Struktur

```text
backend/
+-- apps/
|   +-- api/
|   |   +-- main.py
|   |   +-- wiring.py
|   |   +-- live_coaching_lifecycle.py
|   |   +-- live_coaching_event_publisher.py
|   +-- device_agent/
|
+-- features/
|   +-- person/
|   +-- check_in/
|   +-- training/
|   +-- workout/
|   +-- telemetry/
|   +-- coaching/
|   +-- speech/
|
+-- adapters/
+-- alembic/
+-- scripts/
+-- tests/
```

Feature-interne Struktur:

```text
feature/
+-- domain/          fachliche Modelle, Enums und Ports
+-- service/         Use Cases und Anwendungslogik
+-- api/
|   +-- contracts/   HTTP-/WebSocket-Verträge
|   +-- router.py
+-- persistence/     SQLAlchemy / Repositories
+-- adapters/        technische Implementierungen, falls feature-spezifisch
```

## 5.2 Fachliche Features

### `person`

Verantwortet Person und Profil: Anzeigename, Geburtsdatum, Größe, Trainingsziel, optionale maximale Herzfrequenz, Startgewicht und Zielgewicht. Person und Profil sind getrennte 1:1-Aggregate in der Persistenz.

### `check_in`

Verantwortet Tagesform und Gesundheitskontext: Energie, Erholung, Muskelkater, Stress, verfügbare Trainingszeit, aktuelles Gewicht, Schlaf und Schritte einschließlich Historie.

### `training`

Verantwortet Pre-Workout-Entscheidungen. Der aktuelle Aufbau enthält unter anderem:

```text
PreWorkoutCoachingPlanner
ReadinessService
WeightTrendService
WeightGoalProgressService
PreWorkoutReasonBuilder
CoachMessageGenerator (Port)
FallbackCoachMessageGenerator
```

Die Empfehlung umfasst strukturierte Gründe und bleibt fachlich unabhängig von der sprachlichen Formulierung.

### `workout`

Verantwortet Workout-Lebenszyklus, persistierten Status, Dauer, Distanz, Video, Phasen, Summary und Runtime-Zustände.

Relevante Runtime-Zustände:

```text
running
paused
finish_window
overtime
```

### `telemetry`

Verantwortet technische Messdaten und Gerätezustand. Der `TelemetryService` interpretiert eingehende Geräteinformationen, hält den aktuellen Device State und publiziert fachliche `HeartRateSample` an Listener.

### `coaching`

Verantwortet Live-Coaching während des Workouts. HR-Abweichungen werden über Zeit bewertet; zusätzlich erzeugt die Session strukturbezogene Coaching-Ereignisse unabhängig vom Vorhandensein eines HR-Sensors.

### `speech`

Verantwortet Text-to-Speech über einen fachlich neutralen TTS-Port. Die aktuelle lokale Implementierung verwendet Piper.

## 5.3 Pre-Workout-Coaching

```text
Person Profile --------+
Check-in --------------+
Workout History -------+----> PreWorkoutCoachingPlanner
Weight History --------+              |
                                      +--> TrainingRecommendation
                                      +--> reasonCodes
                                      +--> WeightTrend
                                      +--> WeightGoalProgress
                                      +--> ReadinessContext
                                      |
                                      v
                               CoachMessageContext
                                      |
                            +---------+----------+
                            |                    |
                            v                    v
                    deterministic        optional local LLM
                    ReasonBuilder        generator
                            |                    |
                            +---------+----------+
                                      v
                                  Coach Text
```

### Readiness

Die Readiness-Logik berücksichtigt neben subjektiven Check-in-Signalen unter anderem:

- Schlafdauer;
- Tagesschritte;
- kürzlich absolvierte Workouts;
- Trainingsminuten der letzten Tage.

Subjektive Erholungssignale haben weiterhin hohe Priorität. Wenige Schritte führen nicht automatisch zu mehr Training. Kurzer Schlaf oder hohe Vorbelastung können die Dauer begrenzen, ohne alleine einen Recovery-Tag erzwingen zu müssen.

### Gewichtstrend

Der Gewichtstrend ist **beschreibend**. Er darf eine heutige Einheit nicht aggressiver machen.

```text
Weight history
    |
    v
WeightTrendService
    |
    +--> direction
    +--> kg_per_week
    +--> sample_count / span
```

Für einen belastbaren Trend wird eine Mindestanzahl an Messungen und ein Mindestzeitraum gefordert. Fehlen ausreichend Daten, wird dies explizit als unzureichende Datenlage behandelt.

### Gewichtsfortschritt

`WeightGoalProgress` beschreibt Start, aktuelles Ziel, verlorenes Gewicht und prozentualen Fortschritt. Prozentwerte werden für die Darstellung begrenzt; unplausible oder fehlende Zielkonfiguration erzeugt keinen erfundenen Fortschritt.

## 5.4 Live-Coaching-Bausteine

```text
HeartRateDeviationTracker
    -> misst Dauer einer HR-Abweichung

LiveCoachingEngine
    -> NONE / INCREASE_INTENSITY / REDUCE_INTENSITY

LiveCoachingService
    -> Tracker + Engine

LiveCoachingSession
    -> konkretes Workout
    -> elapsedSeconds
    -> aktive Phase
    -> Runtime-State
    -> HR-Samples
    -> Struktur-Events

LiveCoachingCoordinator
    -> verwaltet genau eine aktive Session

LiveCoachingLifecycle
    -> verbindet Workout, Runtime und Telemetrie
       im Composition Root

LiveCoachingEventPublisher
    -> serialisiert fachliche Events
       für /ws/coaching
```

Struktur-Events werden über einen gemeinsamen `structure_handler` weitergegeben. Dazu gehören aktuell:

```text
coaching.phase_started
coaching.phase_ending
coaching.workout_halfway
```

Runtime-Events umfassen insbesondere Pause und Resume. Die Runtime-Aktualisierung ist nicht an das Auftreten eines Struktur-Events gekoppelt.

## 5.5 Frontend

```text
React App
+-- Personenauswahl / Profil
+-- Check-in Wizard
+-- Dashboard
|   +-- Gewichtsverlauf
|   +-- Coach-Bereich
|   +-- CoachAvatar
|   +-- Workout-Historie
+-- Workout
|   +-- Runtime / Video
|   +-- Telemetrie
|   +-- Live-Coaching
|   +-- CoachAvatar
|   +-- Audio-Ausgabe
|   +-- Summary
+-- coaching/
|   +-- WebSocket Parser / Typen
|   +-- useLiveCoaching
|   +-- coachingMessage
|   +-- coachingSpeech
|   +-- useCoachSpeech
|   +-- CoachAvatar
+-- API-Clients
```

Der Coach hat eine visuelle Identität über einen wiederverwendbaren Avatar. Diese Darstellung ist reine Präsentation und enthält keine Fachlogik.

---

# 6. Laufzeitsicht

## 6.1 Check-in

```text
Person
  |
  v
React CheckInWizard
  |
  +---- GET letzter Zustand ----> FastAPI -> Service -> Repository -> SQLite
  |
  +---- Eingabe
  |
  +---- POST Check-in ----------> FastAPI -> Service -> Repository -> SQLite
```

## 6.2 Pre-Workout-Empfehlung

```text
Dashboard
   |
   v
GET Training Recommendation
   |
   v
API Composition
   |
   +--> Person/Profile
   +--> letzter Check-in
   +--> Check-in-Historie
   +--> Workout-Historie
   |
   v
Readiness + WeightTrend + GoalProgress
   |
   v
PreWorkoutCoachingPlanner
   |
   +--> strukturierte Empfehlung
   +--> reasonCodes
   +--> deterministische/fallback Formulierung
   |
   v
Dashboard Coach
```

## 6.3 Workout-Start

```text
Frontend
   |
   | POST /api/workouts/...
   v
Workout Router
   |
   v
WorkoutService
   |
   +--> Repository --> SQLite
   |
   v
LiveCoachingLifecycle
   |
   v
LiveCoachingCoordinator
   |
   v
LiveCoachingSession aktiv
```

## 6.4 Telemetrie bis HR-Coaching

```text
HR Sensor
   |
   v
Device Agent
   |
   | heart_rate.sample
   v
TelemetryService
   |
   +--> Device State
   |
   +--> HeartRateSample
            |
            v
LiveCoachingLifecycle
            |
            v
LiveCoachingCoordinator
            |
            v
LiveCoachingSession
            |
      aktuelle Phase
            |
      Ziel-HR min/max
            |
            v
HeartRateDeviationTracker
            |
            v
LiveCoachingEngine
            |
            v
LiveCoachingDecision
            |
            v
EventPublisher -> /ws/coaching -> Frontend
```

Ein einzelner Wert über oder unter Ziel löst keine sofortige Belastungsanweisung aus. Erst eine anhaltende Abweichung über eine konfigurierbare Dauer führt zu einer Entscheidung.

## 6.5 Phasen- und Milestone-Coaching

Strukturfeedback funktioniert auch ohne HR-Sensor.

```text
Workout Checkpoint
      |
      v
LiveCoachingSession
      |
      +--> Phase gewechselt?
      |       -> phase_started
      |
      +--> Schwelle "1 Minute bis Phasenende" überschritten?
      |       -> phase_ending
      |
      +--> Workout-Halbzeit überschritten?
              -> workout_halfway
      |
      v
LiveCoachingEventPublisher
      |
      v
/ws/coaching
      |
      +--> sichtbare Coach-Nachricht
      +--> Speech Policy
              |
              v
             TTS
```

Schwellen werden als **Überschreitungen** erkannt und nicht durch exakte Sekundenvergleiche. Dadurch geht ein Event nicht verloren, wenn Checkpoints beispielsweise von Sekunde 238 direkt auf 242 springen.

Die letzte Phase wird als solche gekennzeichnet und kann dadurch eine eigene Formulierung erhalten.

## 6.6 Pause / Resume

```text
running
   |
   v
paused
   |
   +--> PAUSE_STARTED
   +--> HR-Coaching suspendieren
   +--> Abweichungstracker zurücksetzen
   |
   v
running
   |
   +--> PAUSE_ENDED
   +--> Tracker frisch starten
   +--> HR-Coaching wieder aktiv
```

Der Runtime-State wird unabhängig davon aktualisiert, ob derselbe Checkpoint ein Struktur-Event erzeugt.

## 6.7 Finish-Window und Overtime

Workout-Runtime und Coaching bleiben getrennte Verantwortlichkeiten. Finish-Window und Overtime sind Runtime-Zustände; normales Belastungscoaching soll dort nicht fälschlich wie in einer aktiven Belastungsphase fortgesetzt werden.

Der persistierte Abschlussstatus wird serverseitig bestimmt:

```text
elapsed < planned
    -> ABORTED

elapsed >= planned
    -> COMPLETED
```

## 6.8 Kein HR-Sensor

```text
Workout läuft
   |
   +--> HR verfügbar
   |       -> HR-Coaching aktiv
   |
   +--> HR nicht verfügbar
           -> kein HR-Coaching
           -> Phasen-/Milestone-Coaching bleibt aktiv
           -> Workout läuft weiter
```

Ein Verbindungsabbruch des Sensors ist damit kein Workout-Abbruch.

## 6.9 Speech- und TTS-Laufzeit

```text
Coaching Event
      |
      v
coachingMessage / coachingSpeech
      |
      v
Speech Policy
      |
      v
POST /api/speech/synthesize
      |
      v
SpeechService
      |
      v
TtsPort
      |
      v
PiperTtsAdapter
      |
      v
WAV Audio
      |
      v
Browser Playback
```

Für strukturbezogene, nicht sicherheitskritische Meldungen werden kurze, aktive Coach-Texte verwendet, beispielsweise:

```text
"Los geht's! Fahr dich locker warm und finde deinen Rhythmus."
"Noch eine Minute! Bleib dran."
"Halbzeit! Die Hälfte ist geschafft. Weiter so."
```

Safety-/HR-Texte bleiben dagegen bewusst nüchtern und eindeutig.

### Piper-Syntheseparameter

Das aktuelle Coach-Preset ist konfigurierbar:

```text
HEALTH_COACH_TTS_LENGTH_SCALE=0.92
HEALTH_COACH_TTS_NOISE_SCALE=0.70
HEALTH_COACH_TTS_NOISE_W_SCALE=0.85
HEALTH_COACH_TTS_VOLUME=1.0
```

Die Werte gehören zur technischen Sprachdarstellung und nicht zur Coaching-Fachlogik.

## 6.10 Lokales LLM

Das LLM wird über eine OpenAI-kompatible lokale HTTP-Schnittstelle angesprochen.

```text
Deterministische Entscheidung
          |
          v
CoachMessageContext
          |
     +----+---------------------+
     |                          |
     v                          v
LocalLlmCoachMessageGenerator  deterministic ReasonBuilder
     |                          |
     +-----------+--------------+
                 v
      FallbackCoachMessageGenerator
                 |
                 v
              Coach Text
```

Ein Timeout, eine Exception oder eine leere Antwort führt zum deterministischen Fallback. Das LLM darf die bereits getroffene Trainingsentscheidung nicht verändern.

Die aktuelle kleine lokale Modellklasse ist ressourcenschonend, aber generative Faktentreue bleibt eine Qualitätsgrenze. Deshalb bleibt die Architektur so ausgelegt, dass faktische Coach-Aussagen auch vollständig ohne LLM erzeugt werden können.

---

# 7. Verteilungssicht

## 7.1 Entwicklung

```text
+---------------------- Entwickler-PC -----------------------+
| React Dev Server                                            |
| FastAPI Backend                                             |
| Device Agent                                                |
| SQLite DB                                                   |
| Piper TTS                                                   |
| llama-server [optional]                                     |
| Bluetooth Hardware [optional]                               |
+-------------------------------------------------------------+
```

## 7.2 Zielbild Appliance

```text
+----------------------- Debian Appliance ----------------------------+
|                                                                      |
|  +------------------+        +--------------------+                   |
|  | Frontend / Kiosk | <----> | FastAPI API        |                   |
|  +------------------+        +----+-----------+---+                   |
|                                  |           |                       |
|                           +------+           +----------------+      |
|                           v                               v           |
|                     +-----+------+                  +-----+------+    |
|                     | SQLite     |                  | Piper TTS  |    |
|                     +------------+                  +------------+    |
|                                  |                                   |
|                         [optional] v                                  |
|                            +-----+------+                             |
|                            | Local LLM  |                             |
|                            | llama-server|                            |
|                            +------------+                             |
|                                                                      |
|  +-------------------+                                               |
|  | Device Agent      | ----> Bluetooth: FTMS / HR                    |
|  +-------------------+                                               |
+----------------------------------------------------------------------+
```

## 7.3 systemd-Abhängigkeiten

```text
Boot
 |
 v
health-coach-prepare.service
 |
 +-----------------------------+
 |                             |
 v                             v
health-coach-llm.service   health-coach-api.service
      [optional]                 |
                                 v
                       health-coach-device-agent.service
```

Die API verwendet für das LLM eine weiche Abhängigkeit (`Wants=` statt `Requires=`). Ein Fehler des LLM-Service darf die API nicht mit herunterziehen.

## 7.4 Provisionierung vs. Boot-Vorbereitung

```text
provision.sh
    = explizites Update / Deployment
    = git pull --ff-only
    = Dependencies
    = Frontend Build
    = TTS-/LLM-Modelle
    = prepare.sh / Migration
    = Service-Restart

prepare.sh
    = Boot-Vorbereitung
    = offline-fähig
    = keine Downloads
    = keine Builds
    = lokale Runtime-Prüfung
    = Alembic-Migration
```

Die vollständigen Befehle, Environment-Dateien und systemd-Units stehen in `DEPLOYMENT.md`.

---

# 8. Querschnittliche Konzepte

## 8.1 Persistenz und Datenintegrität

SQLite-Fremdschlüssel werden erzwungen. Migrationen dürfen fachliche Daten nicht still löschen oder erfinden.

```text
person
  +----< check_in.person_id
  +----< workout.person_id
  +---- person_profile.person_id

workout_video
  +----< workout.video_id

workout
  +----< workout_phase.workout_id
```

Schema-Migrationen und fachliche Seed-/Pflegedaten bleiben getrennt.

## 8.2 Fehlende Messwerte

```text
keine Eingabe  ---> null
unbekannt      -X-> 0
```

Fehlende Werte werden weder in API noch UI als Nullmessung interpretiert.

## 8.3 Optionale Komponenten und Graceful Degradation

```text
HR-Sensor fehlt
    -> kein HR-Coaching
    -> Workout bleibt nutzbar

LLM fehlt / Timeout
    -> deterministischer Coach-Text
    -> Kernfunktion bleibt nutzbar

TTS schlägt fehl
    -> sichtbares Coaching bleibt erhalten
    -> Workout bleibt nutzbar
```

Dies ist ein systemweites Prinzip.

## 8.4 API-Verträge

HTTP- und WebSocket-Verträge sind von Domänenmodellen getrennt. Das Frontend verwendet camelCase. Fachliche Domainobjekte werden nicht ungefiltert als externe Verträge verwendet.

## 8.5 Cross-Feature-Orchestrierung

Nicht gewünscht:

```text
WorkoutService ------> CoachingService
TelemetryService ----> CoachingService
```

Bevorzugt:

```text
                 apps/api
                    |
                    v
          LiveCoachingLifecycle
           /               \
          v                 v
 WorkoutService       TelemetryService
          \                 /
           \               /
            v             v
         LiveCoachingCoordinator
```

## 8.6 Entscheidung und Formulierung

```text
Domain / Planner
    -> Entscheidung + Reason Codes + Fakten

CoachMessageContext
    -> explizite, bereits entschiedene Information

CoachMessageGenerator
    -> Formulierung

FallbackCoachMessageGenerator
    -> garantiert deterministische Rückfallebene
```

Dadurch kann die Formulierung ausgetauscht werden, ohne dass eine generative Komponente Trainingsregeln neu interpretiert.

## 8.7 Speech Policy

Nicht jedes Event muss sofort gesprochen werden. Die Speech Policy entscheidet, ob und wann Audio ausgegeben wird. Eine weitergehende Priorisierung konkurrierender Live-Coaching-Events ist ein sinnvoller nächster Ausbaupunkt.

Zielpriorität:

```text
Safety / Belastungssteuerung
        > Runtime / Pause
        > Phasenwechsel
        > Milestone
        > Motivation
```

## 8.8 Lokale TTS-Architektur

```text
Coach Text
   |
   v
Speech Policy
   |
   v
SpeechService
   |
   v
TtsPort
   |
   +--> PiperTtsAdapter [primär]
   +--> weitere Adapter [später]
```

Piper wird einmal geladen und lokal wiederverwendet. Voice-Modell und Syntheseparameter sind Konfiguration. Downloads gehören in die Provisionierung, nicht in den normalen Boot-Pfad.

## 8.9 Lokale LLM-Architektur

Das LLM ist Infrastruktur hinter einem Port und kein Bestandteil der Domainlogik. Konkrete Runtime und Modell können ersetzt werden, ohne Planner oder Coaching-Engine neu zu entwerfen.

Aktuelle Konfiguration verwendet einen lokalen OpenAI-kompatiblen Server. Das Backend kommuniziert ausschließlich über Loopback mit diesem Service.

## 8.10 Teststrategie

```text
+---------------------------+
| Domain / pure Services    |
| Unit Tests                |
+-------------+-------------+
              v
+-------------+-------------+
| Coordinator / Lifecycle   |
| Integration Tests         |
+-------------+-------------+
              v
+-------------+-------------+
| Repository / API / WS     |
| Integration Tests         |
+-------------+-------------+
              v
+-------------+-------------+
| SQLite Test-DB            |
| Foreign Keys ON           |
+---------------------------+
```

Persistenztests verwenden eine isolierte SQLite-In-Memory-Datenbank aus `tests/conftest.py`. API-Tests dürfen bewusst In-Memory-Repositories verwenden, wenn Persistenz nicht Gegenstand des Tests ist.

## 8.11 Migrationsstrategie

- neue Schemaänderungen erhalten neue Alembic-Revisions;
- bereits veröffentlichte Migrationen werden nicht leichtfertig nachträglich verändert;
- Migrationen reparieren oder löschen fachliche Daten nicht still;
- `alembic upgrade head` ist Teil der Runtime-Vorbereitung und darf idempotent erneut ausgeführt werden.

## 8.12 Architekturdiagramme

Pseudografiken in Markdown sind die portable Referenz:

```text
+-------------+     Komponente/System
| Komponente  |
+-------------+

------>             gerichteter Aufruf/Datenfluss
<----->             bidirektionale Kommunikation
[optional]           optionaler Bestandteil
```

Sie bleiben im Git-Diff, Terminal und einfachen Markdown-Viewern lesbar.

---

# 9. Architekturentscheidungen (ADRs)

## ADR-001 – Package-by-Feature
**Status:** Akzeptiert

Fachliche Module liegen unter `features/`; technische Schichten innerhalb des Features. Gemeinsame Infrastruktur bleibt außerhalb.

## ADR-002 – Service-Schicht heißt `service/`
**Status:** Akzeptiert

Use Cases und Anwendungslogik liegen einheitlich unter `service/`.

## ADR-003 – SQLite als lokale Persistenz
**Status:** Akzeptiert

SQLite unterstützt den lokalen Appliance-Charakter und reduziert Betriebsaufwand.

## ADR-004 – SQLAlchemy und Alembic
**Status:** Akzeptiert

SQLAlchemy übernimmt Datenzugriff, Alembic versionierte Schemaänderungen.

## ADR-005 – SQLite-Fremdschlüssel werden erzwungen
**Status:** Akzeptiert

Verbindungen aktivieren `PRAGMA foreign_keys=ON`.

## ADR-006 – Migrationen erfinden oder löschen keine fachlichen Daten still
**Status:** Akzeptiert

Nicht eindeutig reparierbare Inkonsistenzen führen lieber sichtbar zum Fehler als zu stiller Datenmanipulation.

## ADR-007 – Person und PersonProfile getrennt
**Status:** Akzeptiert

Stabile Identität bleibt von erweiterbaren Profildaten getrennt.

## ADR-008 – Gesundheitswerte über Check-ins historisieren
**Status:** Akzeptiert

Zeitabhängige Werte wie Gewicht, Schlaf und Schritte gehören in die Check-in-Historie.

## ADR-009 – Fehlende Gesundheitswerte als `null`
**Status:** Akzeptiert

Unbekannte Werte werden nicht als `0` erfunden.

## ADR-010 – Telemetrie-Hardware über Adapter
**Status:** Akzeptiert

FTMS und HR bleiben technische Adapter hinter fachlichen Telemetrie-Abstraktionen.

## ADR-011 – API und Device Agent als getrennte Prozesse
**Status:** Akzeptiert

HTTP-Anwendung und Hardware-Lebenszyklus bleiben getrennt deploybar und restartbar.

## ADR-012 – Gewichtsdiagramm leichtgewichtig ohne Chart-Bibliothek
**Status:** Akzeptiert

Die aktuelle Darstellung bleibt bewusst einfach; bei steigender Komplexität wird die Entscheidung neu bewertet.

## ADR-013 – Architekturdiagramme als Markdown-Pseudografik
**Status:** Akzeptiert

Diagramme bleiben versionskontrollierbar und werkzeugunabhängig lesbar.

## ADR-014 – UI zunächst Maus, Sprache als Erweiterung
**Status:** Akzeptiert

Alle Kernpfade bleiben per Maus bedienbar. Sprache ist ein ergänzender Kanal.

## ADR-015 – Persistierter Workout-Endstatus wird serverseitig bestimmt
**Status:** Akzeptiert

Das Frontend meldet Ist-Zeit und Distanz; die Domain entscheidet `completed` vs. `aborted`.

## ADR-016 – Coaching zunächst deterministisch und regelbasiert
**Status:** Akzeptiert

Safety und Trainingslogik müssen reproduzierbar und unit-testbar bleiben.

## ADR-017 – Live-Coaching bleibt von Workout-Runtime getrennt
**Status:** Akzeptiert

Runtime beantwortet „Was passiert zeitlich?“, Coaching beantwortet „Wie ist die aktuelle Belastung zu bewerten?“.

## ADR-018 – Heart-Rate-Abweichungen werden zeitlich bewertet
**Status:** Akzeptiert

Ein einzelner HR-Wert löst keine Belastungsanweisung aus.

## ADR-019 – Cross-Feature-Coaching-Orchestrierung liegt im App-Layer
**Status:** Akzeptiert

`LiveCoachingLifecycle` verbindet Workout, Telemetrie und Coaching im Composition Root.

## ADR-020 – Rohtelemetrie und Coaching-Events nutzen getrennte WebSockets
**Status:** Akzeptiert

Die UI bleibt von Rohdatenanalyse entkoppelt.

## ADR-021 – Sprachformulierung und Coaching-Entscheidung sind getrennt
**Status:** Akzeptiert

Fachliche Engines erzeugen Entscheidungen/Fakten, nicht zwingend fertige gesprochene Sätze.

## ADR-022 – Speech Policy verhindert akustische Überlastung
**Status:** Akzeptiert

Wiederholungen werden gedrosselt; relevante neue Situationen erhalten Vorrang.

## ADR-023 – Heart Rate ist optional
**Status:** Akzeptiert

Ein fehlender oder ausfallender HR-Sensor darf den Workout-Lebenszyklus nicht abbrechen.

## ADR-024 – SQLAlchemy-Testdatenbanken werden zentral über `conftest.py` erzeugt
**Status:** Akzeptiert

Persistenztests laufen isoliert von Entwicklungs-/Produktivdaten.

## ADR-025 – Schema-Migrationen enthalten keine versteckten Workout-Video-Seeds
**Status:** Akzeptiert

Schema und fachliche Seed-Daten werden getrennt behandelt.

## ADR-026 – Pause/Resume sind eigene Coaching-Ereignisse
**Status:** Akzeptiert

Pause/Resume werden nicht als HR-Entscheidungen missbraucht; HR-Tracking wird passend suspendiert/zurückgesetzt.

## ADR-027 – Lokales LLM ergänzt, ersetzt aber keine deterministische Coaching-Entscheidung
**Status:** Akzeptiert

Ein LLM darf formulieren oder erklären, aber weder Safety-Regeln noch Trainingsentscheidung überschreiben.

## ADR-028 – Lokale TTS-Engine hinter austauschbarem Port; Piper als erste Implementierung
**Status:** Akzeptiert

TTS-Infrastruktur bleibt von Coaching und Speech Policy getrennt. Piper ist die aktuelle CPU-taugliche Offline-Implementierung.

## ADR-029 – Pre-Workout-Entscheidung und Coach-Formulierung sind getrennte Verträge
**Status:** Akzeptiert

`CoachMessageContext` und `CoachMessageGenerator` verhindern, dass ein Formulierungsadapter direkten Zugriff auf Planner-/Persistenzinternas benötigt.

## ADR-030 – Gewichtstrend ist beschreibend und erhöht die Trainingslast nicht automatisch
**Status:** Akzeptiert

Gewichtsverlust ist ein langfristiges Ziel, aber kurzfristige Trainingsbelastung wird primär von Readiness und Trainingsregeln bestimmt.

## ADR-031 – Workout-Strukturfeedback wird als fachliches Live-Coaching-Event modelliert
**Status:** Akzeptiert

Phasenstart, Phasenende und Halbzeit sind keine Frontend-Timer-Hacks, sondern serverseitig erzeugte Coach-Ereignisse.

## ADR-032 – Deployment und Boot-Vorbereitung sind getrennt
**Status:** Akzeptiert

`provision.sh` darf Netzwerk, Dependencies, Build und Modell-Downloads durchführen. `prepare.sh` bleibt offline-fähig und auf lokale Runtime-Vorbereitung begrenzt.

## ADR-033 – TTS-Prosodie ist technische Konfiguration
**Status:** Akzeptiert

Tempo, Variation und Lautstärke werden über `PiperSynthesisSettings` bzw. Environment-Variablen eingestellt und nicht in Fachlogik eingebaut.

---

# 10. Qualitätsanforderungen

- Referenzverletzungen werden durch DB-Constraints sichtbar.
- Fachliche Regeln sind überwiegend als pure Services/Domainlogik testbar.
- Cross-Feature-Verknüpfungen befinden sich im Composition Root.
- Fehlende Messwerte werden nicht erfunden.
- Optionale Sensorik blockiert keine zentrale Workout-Funktion.
- Ein einzelner HR-Messwert erzeugt keine aggressive Reaktion.
- Gewichtstrends verändern nicht unkontrolliert die Tagesbelastung.
- LLM-Ausfall oder Timeout führt zu Fallback statt Funktionsverlust.
- TTS-Ausfall darf sichtbares Coaching und Workout nicht blockieren.
- Coaching-Ausgaben werden gedrosselt bzw. perspektivisch priorisiert.
- Produktivstart und Update sind reproduzierbar dokumentiert.
- Modelle werden nicht beim normalen Boot aus dem Internet geladen.

---

# 11. Risiken und technische Schulden

| Thema | Aktuelles Risiko / Schuld | Nächster sinnvoller Schritt |
|---|---|---|
| Live-Coaching-Dichte | mehrere Events können zeitlich kollidieren | zentrale Priorisierung und Deduplizierung |
| LLM-Faktentreue | kleine lokale Modelle können Fakten sprachlich verzerren | LLM nur auf sichere Rollen begrenzen / stärkere Validierung / größeres Modell testen |
| LLM-Latenz | CPU-Inferenz kann mehrere Sekunden benötigen | nicht blockierende Nutzung für optionale Inhalte |
| Piper-Prosodie | Voice kann trotz Tuning monoton wirken | Presets feinjustieren, alternative Voice/Engine evaluieren |
| HR-Reconnect | Unterbrechung und Wiederverbindung weiter beobachten | explizite Availability-Events / Tests |
| TTS-Queue | konkurrierende Meldungen können Audio überlagern | Priorität, Cancel/Replace, Queue-Policy |
| Adaptive Workouts | automatische Anpassung noch nicht umgesetzt | AdjustmentPolicy + Safety-Grenzen zuerst |
| Frontend/Deployment | Frontend-Service sollte vollständig als Repo-Referenz gepflegt werden | systemd-Unit in `deploy/systemd/` versionieren |
| Dokumentation | frühere parallele arc42-Dateien erzeugten Drift | diese Datei als einzige kanonische arc42-Doku verwenden |
| Kiosk/Recovery | Appliance-Betrieb kann weiter gehärtet werden | Health Checks, Watchdog, Update/Rollback |

---

# 12. Glossar

| Begriff | Bedeutung |
|---|---|
| Check-in | Tagesform plus optionale Gesundheitswerte |
| Readiness | zusammengefasster Kontext zur heutigen Belastbarkeit |
| WeightTrend | beschreibende Gewichtsveränderung über ein definiertes Fenster |
| WeightGoalProgress | Fortschritt zwischen Start- und Zielgewicht |
| Device Agent | separater Prozess für Hardware/Bluetooth |
| FTMS | Bluetooth Fitness Machine Service |
| HR | Heart Rate |
| Workout Phase | Teilabschnitt eines Workouts |
| Workout Runtime | zeitlicher Zustand eines laufenden Workouts |
| Live Coaching | Echtzeitbewertung von Workout, Struktur und Telemetrie |
| CoachingDecision | fachliche Entscheidung der Coaching Engine |
| Structure Event | zeit-/phasenbezogenes Coaching-Event ohne notwendige HR-Abhängigkeit |
| Speech Policy | entscheidet, ob/wann ein Coach-Event gesprochen wird |
| TTS | Text-to-Speech |
| Piper | lokale TTS-Engine / aktueller TTS-Adapter |
| CoachMessageContext | expliziter Vertrag bereits entschiedener Fakten zur Formulierung |
| CoachMessageGenerator | Port für Coach-Textformulierung |
| LLM | lokales Large Language Model als optionale Formulierungsschicht |
| llama-server | lokale OpenAI-kompatible LLM-Runtime |
| Appliance | lokal betriebenes eigenständiges Coach-Gerät |
| Composition Root | zentrale Verdrahtung von Cross-Feature-Abhängigkeiten |
| Deviation Tracker | misst die Dauer einer kontinuierlichen HR-Abweichung |
| Provisionierung | Installation/Update von Code, Dependencies, Assets und Modellen |
| Prepare | offline-fähige Runtime-Vorbereitung vor Service-Start |

---

# 13. Funktionsliste

Legende: **Vorhanden**, **Teilweise/optional**, **Geplant**.

| Bereich | Funktion | Status |
|---|---|---|
| Personen | mehrere Personen / stabile IDs | Vorhanden |
| Profil | Basisdaten, Trainingsziel, Start-/Zielgewicht, optionale max. HF | Vorhanden |
| Check-in | Energie, Erholung, Muskelkater, Stress, Zeit | Vorhanden |
| Check-in | Gewicht, Schlaf, Schritte, Historie | Vorhanden |
| Training | deterministische Pre-Workout-Empfehlung | Vorhanden |
| Training | Readiness aus subjektiven und objektiven Signalen | Vorhanden |
| Training | WeightTrend | Vorhanden |
| Training | WeightGoalProgress | Vorhanden |
| Training | strukturierte Reason Codes | Vorhanden |
| Dashboard | Coach-Bereich mit Empfehlung | Vorhanden |
| Dashboard | Gewichtsverlauf / Zielbezug | Vorhanden |
| Dashboard | Coach-Avatar | Vorhanden |
| Workout | Lebenszyklus, Dauer, Distanz | Vorhanden |
| Workout | Runtime running/paused/finish_window/overtime | Vorhanden |
| Workout | Summary / serverseitiger Abschlussstatus | Vorhanden |
| Telemetrie | FTMS / HR | Vorhanden |
| Telemetrie | separater Device Agent | Vorhanden |
| Coaching | HR-Zielbereich und Deviation Tracker | Vorhanden |
| Coaching | `/ws/coaching` | Vorhanden |
| Coaching | Pause/Resume | Vorhanden |
| Coaching | Phasenstart | Vorhanden |
| Coaching | Phasenende / noch eine Minute | Vorhanden |
| Coaching | Halbzeit | Vorhanden |
| Coaching | Speech Policy | Vorhanden, Ausbau geplant |
| Speech | lokale Piper-TTS | Vorhanden |
| Speech | konfigurierbare Prosodie | Vorhanden |
| LLM | LocalLlmCoachMessageGenerator | Teilweise/optional |
| LLM | deterministischer Fallback | Vorhanden |
| LLM | frei formuliertes sicherheitskritisches Live-Coaching | Nicht vorgesehen |
| Betrieb | Debian/systemd | Vorhanden |
| Betrieb | `provision.sh` / `prepare.sh` | Vorhanden |
| Betrieb | lokaler LLM-Service | Vorhanden/optional |
| Coaching | zentrale Event-Priorisierung | Geplant |
| Coaching | weitere Signale wie Kadenz/Leistung | Geplant |
| Workout | automatische adaptive Anpassung | Geplant |
| Sprache | Spracheingabe | Geplant |
| Betrieb | Rollback/Watchdog/Health-Härtung | Geplant |

---

# 14. Feature-Roadmap

## Phase A – Coaching-Qualität und Event-Priorisierung

Nächster sinnvoller Schwerpunkt:

```text
Incoming Coach Events
        |
        v
Priority / Dedupe Policy
        |
        +--> Safety / HR
        +--> Pause / Runtime
        +--> Phase
        +--> Milestone
        +--> Motivation
        |
        v
Speech Queue
```

Ziele:

- konkurrierende Meldungen priorisieren;
- Audio nicht überlagern;
- wiederholte oder veraltete Meldungen verwerfen;
- Feedback-Dichte erhöhen, ohne den Coach nervig zu machen.

## Phase B – Live-Coaching ausbauen

- Kadenz und Leistung als weitere Signale;
- Sensorverfügbarkeit expliziter modellieren;
- „gute Konstanz“ und weitere positive Rückmeldungen nur aus belastbaren Signalen;
- konfigurierbare Feedback-Frequenz.

## Phase C – Adaptives Workout

```text
Live Coaching Decision
          |
          v
Adjustment Policy
          |
    +-----+------+
    |            |
    v            v
 Dauer        Intensität
    \            /
     +----+-----+
          v
   Workout Runtime
```

Vor jeder automatischen Anpassung stehen explizite Safety- und Begrenzungsregeln.

## Phase D – Coach-Sprache und Dialog

- TTS-Preset weiter optimieren;
- alternative lokale Voice/Engine evaluieren;
- LLM zunächst für nicht sicherheitskritische Motivation/Erklärung nutzen;
- später Spracheingabe als zusätzlicher, niemals alleiniger Bedienpfad.

## Phase E – Appliance-Härtung

- systemd-Health-Checks;
- Watchdog/Recovery;
- Backup-Strategie;
- reproduzierbares Update/Rollback;
- Wartungsmodus.

---

# 15. Entwicklerleitfaden: Wo gehört neue Logik hin?

```text
Ist es eine fachliche Regel?
    -> domain/ oder service/ des Features

Ist es ein HTTP-/WebSocket-Vertrag?
    -> api/contracts/

Ist es Persistenz?
    -> persistence/

Ist es Hardware-/Transporttechnik?
    -> adapter / device agent

Verbindet es mehrere Features?
    -> apps/api / Composition Root

Ist es reine Darstellung?
    -> Frontend-Komponente

Ist es Frontend-Orchestrierung?
    -> Hook / Frontend-Service

Ist es Audioerzeugung?
    -> speech adapter hinter TtsPort

Ist es Formulierung eines bereits entschiedenen Coach-Inhalts?
    -> CoachMessageGenerator / ReasonBuilder

Entscheidet es Trainingslast oder Safety?
    -> niemals direkt im LLM-Adapter
```

Beispiele:

```text
"Nach anhaltender HR-Abweichung Intensität reduzieren"
    -> coaching/service

"Kurzer Schlaf begrenzt heute die Dauer"
    -> training/service / Readiness

"Workout ist ab Sollzeit completed"
    -> workout/service

"Phase hat gewechselt"
    -> LiveCoachingSession / domain event

"Event als JSON über WebSocket senden"
    -> apps/api / EventPublisher

"Coach-Meldung im Browser anzeigen"
    -> frontend/coaching

"Soll die Meldung jetzt gesprochen werden?"
    -> Speech Policy

"Wie schnell / lebendig spricht Piper?"
    -> TTS-Konfiguration
```

---

# 16. Pflegehinweise

1. **Diese Datei ist die einzige kanonische arc42-Dokumentation.** Neue Varianten mit Suffixen wie `-aktuell`, `-tts` oder `-llm-plan` sollen nicht mehr parallel gepflegt werden.
2. Implementierte Änderungen aktualisieren mindestens Statusübersicht, Funktionsliste und betroffene Laufzeit-/Bausteinsicht.
3. Relevante Architekturentscheidungen erhalten oder aktualisieren einen ADR.
4. Ersetzte Entscheidungen werden als ersetzt markiert; Historie wird nicht still überschrieben.
5. Geplante Funktionen werden nicht als vorhanden dokumentiert.
6. Deployment-Details bleiben in `DEPLOYMENT.md`; diese Doku beschreibt die Architektur und referenziert den Betriebsleitfaden.
7. Neue Cross-Feature-Abhängigkeiten werden bevorzugt im Composition Root orchestriert.
8. Neue Coaching-Regeln benötigen Unit-Tests und nachvollziehbare Reason Codes.
9. Optionale Komponenten müssen ein definiertes Degradationsverhalten besitzen.
10. Sicherheit, Trainingsentscheidung und generative Formulierung bleiben getrennte Verantwortlichkeiten.

---

# 17. Verwandte Dokumentation

```text
arc42-digital-fitness-coach.md   -> diese kanonische Architekturreferenz
DEPLOYMENT.md                    -> Debian, systemd, Provisionierung und Betrieb
LOCAL-LLM.md                     -> lokale LLM-Runtime und Modellbetrieb
HOWTO-Entwicklungsumgebung.md    -> Entwicklungssetup
README.md                        -> Projekteinstieg
backend/docs/websockets.md       -> WebSocket-Verträge / technische Details
```

Die früheren arc42-Varianten können nach erfolgreicher Übernahme in Git archiviert oder entfernt werden, damit Architekturänderungen künftig an genau einer Stelle gepflegt werden.
