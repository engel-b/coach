# Digital Fitness Coach – arc42-Architekturdokumentation

> **Kanonische Dokumentation**  
> Sie beschreibt den **implementierten Stand**, ausdrücklich gekennzeichnete **optionale/experimentelle Bausteine** sowie die **geplante Weiterentwicklung**. Deployment-Details werden ergänzend in `DEPLOYMENT.md` gepflegt.

---

## Dokumentstatus auf einen Blick

| Bereich | Status | Aktueller Stand |
|---|---|---|
| Personen / Profile | ✅ Vorhanden | Mehrpersonenbetrieb, Profil, Trainingsziel, Start-/Zielgewicht, optionale maximale HF |
| Check-in | ✅ Vorhanden | Energie, Erholung, Muskelkater, Stress, verfügbare Zeit, Gewicht, Schlaf, Schritte, Historie |
| Trainingsempfehlung | ✅ Vorhanden | deterministischer Pre-Workout-Planner mit Readiness, Gewichtstrend und Gewichtsfortschritt |
| Workout | ✅ Vorhanden | Phasen, Runtime-State, Pause, Finish-Window, Overtime, Persistenz, Summary und Videozuordnung |
| Trainingsvideos | ✅ Vorhanden | dateibasiertes Videoverzeichnis, Katalog-Synchronisation, Verwaltung, personenspezifische Auswahl und Nutzungshistorie |
| Telemetrie | ✅ Vorhanden | FTMS + Heart Rate über separaten Device Agent; Sensorik optional |
| Live-Coaching | ✅ Vorhanden | HR-Abweichung, Pause/Resume, Phasenwechsel, Phasenende, Halbzeit, WebSocket-Events |
| TTS | ✅ Vorhanden | lokale Piper-Synthese hinter Port/Adapter; konfigurierbares Coach-Preset |
| Coach-Avatar | ✅ Vorhanden | wiederverwendbarer Avatar im Dashboard und Workout-Frontend |
| Lokales LLM | 🧪 Optional / experimentell | lokaler OpenAI-kompatibler Adapter mit Timeout und deterministischem Fallback |
| Appliance-Deployment | ✅ Vorhanden / im Ausbau | Debian, Caddy, systemd, `provision.sh`, `prepare.sh`, API/Device-Agent/LLM als Services |
| Adaptive Workout-Anpassung | 🧭 Geplant | deterministische Adjustment-/Safety-Policy vor automatischer Änderung |
| Spracheingabe | 🧭 Geplant | Sprache als zusätzlicher Interaktionskanal, nicht als einziger Bedienpfad |

---

# 1. Einführung und Ziele

## 1.1 Aufgabenstellung

Der **Digital Fitness Coach** ist eine lokal betriebene Fitness- und Gesundheitsanwendung für mehrere Personen. Sie unterstützt den vollständigen Trainingsablauf von Personenauswahl und täglichem Check-in über Trainingsempfehlung und Workout-Durchführung bis zu Live-Telemetrie, Coaching, Sprachausgabe und Trainingshistorie.

Der funktionale Kern umfasst insbesondere:

- Personen und Profile mit Trainingsziel sowie Start-/Zielgewicht,
- tägliche Check-ins mit subjektiven und optionalen objektiven Gesundheitswerten,
- deterministische Pre-Workout-Empfehlungen,
- strukturierte Workouts mit Phasen und Runtime-Zuständen,
- Heart-Rate- und FTMS-Telemetrie über einen separaten Device Agent,
- Live-Coaching mit serverseitig erzeugten Coaching-Ereignissen,
- lokale TTS-Ausgabe über Piper,
- optionale lokale LLM-Formulierung mit deterministischem Fallback,
- einen lokalen Trainingsvideo-Katalog mit Synchronisation des Dateisystems,
- lokalen Appliance-/Kiosk-Betrieb unter Debian.

Das System soll nicht nur Messwerte anzeigen, sondern auf Basis von **Profil, Tagesform, Trainingshistorie, Workout-Phase und Live-Telemetrie** nachvollziehbar reagieren. Dabei gilt als wichtigstes Architekturprinzip:

```text
Deterministische Fachlogik entscheidet, WAS gilt und WAS passieren darf.
Optionale generative Komponenten dürfen höchstens beeinflussen, WIE etwas formuliert wird.
```

Das gilt insbesondere für Trainingsbelastung, Safety-Grenzen, Gewichtsinterpretation und Live-Coaching. Kernfunktionen sollen ohne Cloud-Abhängigkeit funktionieren. Optionale Komponenten wie HR-Sensor, TTS oder lokales LLM dürfen den Workout-Kern nicht unnötig blockieren.

## 1.2 Qualitätsziele

| Priorität | Ziel | Konsequenz |
|---:|---|---|
| 1 | Zuverlässigkeit | Datenintegrität, reproduzierbarer Start, saubere Migrationen, robuste Fallbacks |
| 2 | Nachvollziehbare Coaching-Logik | deterministische, testbare Regeln und explizite Gründe |
| 3 | Wartbarkeit | Package-by-Feature, klare Ports/Adapter, kleine Verantwortlichkeiten |
| 4 | Lokaler Betrieb | Kernfunktionen offline und ohne Cloud-Abhängigkeit |
| 5 | Bedienbarkeit | große klare UI, Coach-Feedback sichtbar und hörbar, Maus als vollständiger Bedienpfad |
| 6 | Erweiterbarkeit | LLM, TTS, Sensorik und weitere Coaching-Signale austauschbar ergänzbar |
| 7 | Verständlichkeit | Architekturdiagramme, ADRs, explizite Verträge und konsistente Entwicklerdokumentation |

## 1.3 Stakeholder

| Stakeholder | Interesse / Erwartung |
|---|---|
| Trainierende Personen | einfache Bedienung, gut lesbare Workout-Anzeige, nachvollziehbares Coaching und verlässliche Trainingsdaten |
| Betreiber / Administrator | automatischer Start, kontrollierte Updates, lokale Datenhaltung, nachvollziehbare Logs und einfache Wiederherstellung |
| Entwickler | klare Modulgrenzen, automatisierte Tests, reproduzierbarer Build und geringe Kopplung an Hardware/Frameworks |
| Geräteintegratoren | stabile Ports, normalisierte Telemetrie und testbare Parser/Adapter |
| Wartung / Support | Diagnose über systemd, journalctl, Health-Endpunkt und reproduzierbare Servicezustände |

## 1.4 Nicht-Ziele und Grenzen

Der Coach ist **kein medizinisches Diagnosesystem**. Er darf Trainings- und Gesundheitsdaten für Fitness-Coaching verwenden, soll aber keine Diagnosen oder unbelegten medizinischen Ursachen behaupten.

Gewichtsverlauf und Zielgewicht werden beschreibend ausgewertet. Ohne explizit konfigurierte Ziel-Abnahmerate wird aus einem langsameren oder schnelleren Gewichtsverlauf **keine automatische Intensivierung des Trainings** abgeleitet.

Aktive automatische Bike-Steuerung ist derzeit nicht Bestandteil des stabilen Kerns. Lesen von Telemetrie und aktive Gerätesteuerung bleiben getrennte Fähigkeiten.

---

# 2. Randbedingungen

## 2.1 Technische Randbedingungen

- Backend: Python, FastAPI, Pydantic, SQLAlchemy, Alembic
- Persistenz: SQLite
- Frontend: React + TypeScript + Vite
- Tests: pytest / mypy / Ruff im Backend, Vitest / ESLint im Frontend
- Device Agent: separater Python-Prozess auf Basis von `asyncio`/Bleak
- Bluetooth: FTMS und Heart Rate
- TTS: lokale Piper-Engine hinter einem Port/Adapter
- Lokales LLM: OpenAI-kompatible HTTP-Schnittstelle, aktuell über `llama-server`
- Produktion: Debian, systemd und Caddy
- Entwicklung: Windows und Linux
- Node.js: 24 LTS; Projektuntergrenze `>=24.15.0 <25`

Zielhardware der aktuellen Appliance ist ein Lenovo ThinkCentre M900z mit Intel Core i3-6100 und 16 GB RAM. Eine dedizierte GPU wird weder für den Kernbetrieb noch für TTS vorausgesetzt.

## 2.2 Organisatorische und betriebliche Randbedingungen

Die Architektur wird inkrementell weiterentwickelt. Dokumentation, Build, Tests, Migrationen und Deployment sind Bestandteil des Produkts und werden gemeinsam mit dem Code versioniert.

Die Produktionsinstallation ist ein Git-Checkout unter `/opt/health-coach`. Laufzeitdaten liegen innerhalb des dafür vorgesehenen `data/`-Baums und werden nicht als Quellcode behandelt:

```text
/opt/health-coach/data/
├── db/
├── models/
│   ├── llm/
│   └── piper/
└── videos/
```

Die produktiven Prozesse laufen getrennt:

```text
health-coach-prepare.service
health-coach-api.service
health-coach-device-agent.service
health-coach-llm.service       [optional]
Caddy                           [statische UI + Reverse Proxy]
Chromium-Kiosk                  [grafische Benutzersitzung]
```

`provision.sh` ist der explizite Update-/Deployment-Pfad und darf Netzwerkzugriff, Dependency-Installation, Builds und Modell-Provisionierung durchführen. `prepare.sh` ist die offline-fähige Boot-Vorbereitung und beschränkt sich auf lokale Runtime-Prüfung und Datenbankmigrationen.

## 2.3 Konventionen

- Backend-interne Python-Namen verwenden `snake_case`.
- JSON-Verträge und TypeScript verwenden `camelCase`.
- Beispiel: `file_path` im Backend entspricht `filePath` im API-/Frontend-Vertrag.
- Domänenobjekte importieren keine FastAPI-, SQLAlchemy-, Bleak- oder React-Typen.
- Datenbankschemaänderungen erfolgen ausschließlich über Alembic-Migrationen.
- Fehlende fachliche oder sensorische Werte bleiben optional/`null`; sie werden nicht als `0` oder durch Schätzwerte erfunden.
- Cross-Feature-Orchestrierung gehört in den App-/Composition-Root.
- Frontend-Code verwendet relative `/api`, `/ws` und `/videos`-Pfade und kennt Produktionsports nicht.
- Neue Hardware wird über Adapter integriert und vor Übergabe an Domain/UI normalisiert.

## 2.4 Fachliche Randbedingungen

- ein fehlender HR-Sensor verhindert kein Workout;
- Coaching-Entscheidungen werden serverseitig erzeugt;
- Workout-Status wird serverseitig final bestimmt;
- Browser und Backend kommunizieren über explizite HTTP-/WebSocket-Verträge;
- LLM und TTS sind austauschbare technische Komponenten und keine fachlichen Entscheidungsträger;
- Workout-Videos werden in der Datenbank mit einem Pfad relativ zum konfigurierten Video-Root gespeichert; die Browser-URL wird daraus abgeleitet.

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

Verantwortet Person und Profil: Anzeigename, Geburtsdatum, Größe, Trainingsziel, optionale maximale Herzfrequenz, optionaler Ruhepuls, Startgewicht und Zielgewicht. Person und Profil sind getrennte 1:1-Aggregate in der Persistenz.

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

Der Workout-Video-Katalog synchronisiert ein konfiguriertes Video-Root mit der Datenbank. Neue Dateien werden katalogisiert, wieder erschienene Dateien reaktiviert und fehlende Dateien inaktiv markiert. Ein vollständig fehlendes/unmountbares Video-Root führt nicht zu einer pauschalen Deaktivierung des Katalogs. Verwaltung zeigt aktive und inaktive Einträge; die personenspezifische Trainingsauswahl liefert nur aktive Videos und kann Nutzungshistorie/zuletzt verwendetes Video berücksichtigen.

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

### Personalisierte Herzfrequenz-Zielbereiche

Die Trainingsphasen verwenden eine zentrale `HeartRateTargetPolicy`. Ist ein persönlicher Ruhepuls im Profil hinterlegt, werden Zielbereiche aus der Herzfrequenzreserve (`HFmax - Ruhepuls`) abgeleitet. Ein hoher oder niedriger Ruhepuls wird für diese Berechnung auf einen konservativen Referenzbereich begrenzt, damit er die Trainingsziele nicht unbegrenzt verschiebt. Fehlt der Ruhepuls, bleibt die bisherige Prozent-von-HFmax-Berechnung als kompatibler Fallback aktiv.

Der Ruhepuls kann zusätzlich pro Check-in als tatsächlich an diesem Tag gemessener Wert erfasst werden. Eine `RestingHeartRateBaselineService` verwendet bei mindestens drei aktuellen Messungen den Median der letzten Messwerte als robuste persönliche Baseline; einzelne Ausreißer wirken dadurch weniger stark. Solange nicht genügend Messungen vorhanden sind, bleibt der manuelle Profilwert der Fallback. Der Check-in-Wert wird im UI bewusst nicht aus dem Vortag vorbelegt, damit nicht versehentlich derselbe alte Wert mehrfach als neue Messung in die Baseline eingeht.

Die Zielbereiche beschreiben die gewünschte Trainingsbelastung und sind keine medizinisch garantierten Sicherheitsgrenzen. Die Trainingsempfehlung liefert die verwendete Berechnungsgrundlage explizit an das Frontend: Methode, HFmax, den hinterlegten Ruhepuls und gegebenenfalls den konservativ begrenzten Ruhepuls-Rechenwert. Dadurch kann die UI nachvollziehbar erklären, wie die angezeigten Zielbereiche zustande kommen.

Live-Coaching bewertet kleine Abweichungen mit einer zusätzlichen Toleranz. Außerhalb dieser Toleranz wird zwischen moderaten und deutlichen Abweichungen unterschieden: moderate Abweichungen müssen länger anhalten, deutliche Abweichungen dürfen nach einer kürzeren Persistenzzeit eine Coaching-Aktion auslösen. Die Speech Policy drosselt wiederholte gleichartige Hinweise; eine Eskalation von moderat auf deutlich darf unmittelbar erneut gesprochen werden. HFmax bzw. davon unabhängige Schutzregeln bleiben vom Ruhepuls unberührt.

### Herzfrequenz-Reaktion aus der Workout-Historie

Während eines laufenden Workouts werden Herzfrequenzwerte der Hauptphase zu einer kompakten `WorkoutHeartRateSummary` verdichtet. Persistiert werden keine vollständigen Rohdatenreihen, sondern nur Stichprobenanzahl, durchschnittliche und maximale Herzfrequenz sowie die prozentualen Anteile unterhalb, innerhalb und oberhalb des für die jeweilige Hauptphase geplanten Zielbereichs.

Eine `HeartRateHistoryService` betrachtet nur abgeschlossene Workouts mit ausreichend vielen Messwerten und verdichtet mehrere aktuelle Einheiten über Medianwerte. Die Historie darf ausschließlich konservativ wirken: Liegt die Herzfrequenz in mehreren auswertbaren Workouts häufig oberhalb des Zielbereichs, kann die heutige Trainingsdauer begrenzt werden. Historisch niedrige Herzfrequenz führt dagegen **nicht** automatisch zu höherer Intensität, höheren Zielpulswerten oder gelockerten Safety-Grenzen.

Die historische Herzfrequenz-Auswertung vergleicht nur Workouts desselben fachlichen Workout-Typs. Der Typ wird bei neuen Workouts persistiert; Altdaten ohne Typ bleiben von dieser Personalisierung ausgeschlossen.

Zusätzlich wird die mittlere Herzfrequenz jedes vergleichbaren Workouts relativ zu dessen damals gültiger Hauptphasen-Zielzone normalisiert: `0 %` entspricht der unteren, `100 %` der oberen Zielgrenze. Dadurch lassen sich Einheiten mit unterschiedlichen absoluten Zielwerten vergleichen. Ab mindestens vier vergleichbaren Workouts werden die ältere und die neuere Hälfte über Medianwerte gegenübergestellt. Eine Verschiebung von mindestens 15 Prozentpunkten wird als höhere bzw. niedrigere relative Herzfrequenz-Reaktion beschrieben; kleinere Änderungen gelten als stabil. Dieser Trend ist rein deskriptiv und darf weder Zielpuls noch Trainingsintensität automatisch erhöhen.

Die Trainingsempfehlung liefert den erkannten Verlauf als strukturierten Kontext an das Frontend. Dadurch bleibt sichtbar, ob die Historie überwiegend im Zielbereich, oberhalb, unterhalb oder uneindeutig war, wie viele Workouts dafür ausgewertet wurden und ob sich die relative Herzfrequenz-Reaktion über vergleichbare Einheiten verschoben hat.

### Herzfrequenz-Reaktion relativ zur Bike-Leistung

Während der Hauptphase wird zusätzlich eine kompakte `WorkoutBikeSummary` aus FTMS-Telemetrie gebildet. Persistiert werden nur Stichprobenanzahl und Mittelwerte für Leistung und Kadenz; vollständige Bike-Rohdatenreihen sind für diese Auswertung nicht erforderlich. Fehlende Sensorwerte bleiben optional und blockieren weder Workout noch Coaching.

Für die historische Interpretation werden nur Workouts mit ausreichend vielen Leistungs-Samples paarweise mit der Herzfrequenz-Reaktion verglichen. Ältere und neuere vergleichbare Einheiten werden über Medianwerte gegenübergestellt. Ändert sich die mittlere Bike-Leistung um höchstens 10 Prozent, gilt die Belastung für diese deskriptive Auswertung als ähnlich. Dadurch kann beispielsweise eine niedrigere relative Herzfrequenz bei annähernd gleicher Leistung von einer niedrigeren Herzfrequenz infolge deutlich geringerer Leistung unterschieden werden.

Die resultierende Einordnung ist ausdrücklich **keine automatische Fitnessbewertung** und verändert Zielpuls, Safety-Grenzen oder Trainingsintensität nicht. Insbesondere wird eine niedrigere Herzfrequenz nur dann als „niedriger bei ähnlicher Leistung“ beschrieben, wenn die historische Leistungsänderung innerhalb der Vergleichstoleranz liegt. Bei deutlich veränderter Leistung wird der HF-Trend als durch die Laständerung mitbedingt bzw. nicht isoliert interpretierbar gekennzeichnet.

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
    = git fetch --prune + optional Branch-Switch + pull --ff-only
    = cleanup-branches.sh
    = Dependencies
    = Frontend Build
    = TTS-/LLM-Modelle
    = Alembic-Migration
    = Konfigurationsabgleich + Service-Restart

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

## 8.13 Fehlerbehandlung

Technische Fehler werden möglichst an Infrastrukturgrenzen behandelt und in fachlich verständliche Zustände übersetzt. BLE-Verbindungsabbrüche ändern den Gerätezustand statt den Workout-Prozess zu beenden; ungültige Telemetrie wird validiert/verworfen; Domänenfehler werden im API-Layer in geeignete HTTP-Statuscodes übersetzt. Optionale LLM-/TTS-/Sensorfehler degradieren die Zusatzfunktion, nicht den Workout-Kern.

## 8.14 Nebenläufigkeit und Shutdown

Der Device Agent verwendet `asyncio` für parallele Geräte-, Backend-WebSocket- und Shutdown-Aufgaben. Beim Shutdown werden Geräte-/BLE-Tasks kontrolliert beendet, damit asynchrone Context Manager Verbindungen freigeben können. Nur ein Device Agent soll gleichzeitig auf ein physisches BLE-Gerät zugreifen.

## 8.15 Logging und Diagnose

Produktionsprozesse schreiben auf stdout/stderr; systemd/journald sammelt die Ausgaben. Wichtige Diagnosepfade sind `systemctl status`, `journalctl -u ...`, der `/health`-Endpunkt sowie direkte Prüfungen der lokalen API-/LLM-Ports. Betriebsdetails stehen in `DEPLOYMENT.md`.

## 8.16 Konfiguration

Umgebungsspezifische Werte liegen außerhalb der Domainlogik. Produktive Environment-Dateien befinden sich unter `/etc/health-coach/`; Repo-Vorlagen werden durch `provision.sh` auf fehlende/veraltete Schlüssel geprüft. Beispiele sind LLM-Endpunkt/-Modell, Piper-Modell und Prosodie, Video-Root und Scan-Intervall. Vorhandene lokale Werte werden beim Schlüsselsync nicht ungefragt überschrieben.

## 8.17 Frontend-Build, Routing und Medien

```text
Development:
React/Vite -> Proxy -> FastAPI

Production:
Chromium -> Caddy :80
             ├─ /api/*    -> FastAPI :8000
             ├─ /ws/*     -> FastAPI :8000
             ├─ /videos/* -> FastAPI :8000 -> konfiguriertes Video-Root
             └─ /*        -> frontend/dist (SPA-Fallback)
```

Das Frontend baut Trainingsvideo-URLs zentral aus `filePath` als `/videos/<filePath>` auf; die Datenbank speichert keine Browser-URL.

## 8.18 Security und Privacy

Gesundheits- und Trainingsdaten verbleiben grundsätzlich lokal, solange keine externe Integration ausdrücklich eingeführt wird. API und lokales LLM binden im Produktivbetrieb an Loopback; Caddy ist der Browser-Einstiegspunkt. Der Kiosk-/Service-Benutzer erhält nur die für Betrieb, Gerätezugriff und Laufzeitdaten erforderlichen Rechte. Secrets dürfen nicht in Git eingecheckt werden; falls Environment-Dateien später Secrets enthalten, sind restriktivere Dateirechte erforderlich.

## 8.19 Update-Konzept

Der Update-Pfad ist explizit und vom Boot getrennt. `provision.sh` führt `git fetch --prune origin` aus, kann optional nur auf einen tatsächlich auf `origin` vorhandenen Zielbranch wechseln, zieht anschließend per `git pull --ff-only`, ruft `cleanup-branches.sh` auf und provisioniert danach Dependencies, Modelle, Build, Konfiguration, Migrationen und Services. Ohne angegebenen Branch bleibt der aktuelle Branch aktiv. Der normale Boot führt kein Git-Update und keine Downloads aus.

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

## ADR-018a – Zielpulsbereiche werden über eine zentrale Policy personalisiert
**Status:** Akzeptiert

Ein optionaler Ruhepuls personalisiert Trainingszonen über die Herzfrequenzreserve. Die Policy begrenzt den für die Berechnung verwendeten Ruhepuls konservativ und fällt bei fehlendem Ruhepuls auf die bisherige HFmax-Prozentlogik zurück. Kleine Abweichungen erhalten im Live-Coaching eine BPM-Toleranz; die zeitliche Abweichungsbewertung bleibt davon getrennt.

## ADR-018b – Workout-Herzfrequenzhistorie darf nur konservativ personalisieren
**Status:** Akzeptiert

Für abgeschlossene Workouts wird eine kompakte Herzfrequenz-Zusammenfassung der Hauptphase persistiert. Mehrere ausreichend belegte Workouts können die heutige Trainingsdauer konservativ begrenzen, wenn die Herzfrequenz wiederholt häufig oberhalb des geplanten Zielbereichs lag. Historisch niedrige Werte dürfen weder die Intensität noch Zielpuls- oder Safety-Grenzen automatisch erhöhen. Vollständige HR-Rohdaten müssen für diese Personalisierung nicht dauerhaft gespeichert werden. Die durchschnittliche Herzfrequenz darf zusätzlich relativ zur jeweils damals gültigen Zielzone normalisiert und als deskriptiver Verlauf über vergleichbare Workouts ausgewertet werden; auch daraus folgt keine automatische Belastungssteigerung.

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

## ADR-034 – Modularer Monolith statt Microservices
**Status:** Akzeptiert

Für die lokale Appliance bleibt der fachliche Kern ein modularer Monolith. Prozessgrenzen werden nur dort eingeführt, wo technische Lebenszyklen sie rechtfertigen (insbesondere Device Agent und optionales LLM).

## ADR-035 – Ports & Adapters als Abhängigkeitsregel
**Status:** Akzeptiert

Domain- und Service-Logik hängen nicht von FastAPI, SQLAlchemy, Bleak, Piper oder llama.cpp ab. Infrastruktur implementiert Ports nach innen.

## ADR-036 – FTMS vor proprietären Bike-Protokollen
**Status:** Akzeptiert

Standardisierte FTMS-Daten werden bevorzugt. Herstellerspezifische Erweiterungen bleiben Adapterdetails und dürfen den fachlichen Telemetrievertrag nicht dominieren.

## ADR-037 – Lesende Bike-Telemetrie und aktive Bike-Steuerung bleiben getrennt
**Status:** Akzeptiert

Ein Gerät kann Telemetrie liefern, ohne dass daraus automatisch die Berechtigung oder Fähigkeit zur aktiven Widerstands-/Leistungssteuerung folgt. Steuerung erhält einen eigenen Lifecycle und Safety-Regeln.

## ADR-038 – Caddy ist der Produktions-Webserver
**Status:** Akzeptiert

Caddy liefert den statischen Vite-Build aus und routet `/api/*`, `/ws/*` und `/videos/*` vor dem SPA-Fallback zu FastAPI. Dadurch bleibt das Frontend von konkreten Produktionsports entkoppelt.

## ADR-039 – systemd verwaltet Produktionsprozesse
**Status:** Akzeptiert

Prepare, API, Device Agent und optionales LLM laufen als systemd-Units. Startreihenfolge, Restart-Policy und Diagnose werden mit Standard-Linux-Werkzeugen abgebildet.

## ADR-040 – Chromium-Kiosk startet in der grafischen Benutzersitzung
**Status:** Akzeptiert

Der Browser wird über Desktop-Autostart/`start-kiosk.sh` gestartet und nicht als systemweiter Backend-Service modelliert, weil er die grafische Benutzersitzung benötigt.

---

# 10. Qualitätsanforderungen

## 10.1 Qualitätsbaum

```text
Qualität
├── Zuverlässigkeit
│   ├── automatischer Appliance-Start
│   ├── Datenintegrität / Migrationen
│   ├── Sensor-/LLM-/TTS-Degradation
│   └── kontrollierter Shutdown
├── Wartbarkeit
│   ├── Package-by-Feature / Ports & Adapter
│   ├── Testbarkeit
│   ├── Geräteerweiterbarkeit
│   └── explizite Verträge
├── Performance
│   ├── Live-Telemetrie-Latenz
│   ├── UI-Reaktionsfähigkeit
│   └── optionale LLM-Latenz darf Kernpfade nicht blockieren
├── Benutzbarkeit
│   ├── Kiosk-Betrieb
│   ├── verständliches Coaching
│   └── vollständiger Maus-Bedienpfad
├── Betriebsfähigkeit
│   ├── systemd/journald
│   ├── kontrolliertes Provisioning
│   ├── Caddy-Validierung
│   └── Diagnose / Health-Checks
└── Datenschutz / Sicherheit
    ├── lokale Datenhaltung
    ├── minimale Netzwerkexposition
    └── minimale Benutzerrechte
```

## 10.2 Qualitätsszenarien

| ID | Situation / Stimulus | Erwartete Reaktion / Akzeptanzkriterium |
|---|---|---|
| QS-01 | normaler Appliance-Start | vorbereitete Services und Caddy starten ohne manuelle Terminalinteraktion; Kiosk kann die Anwendung öffnen |
| QS-02 | neue Heart-Rate-Notification während Workout | Messwert wird normalisiert, übertragen und zeitnah in UI/Coaching verarbeitet; einzelne Messspitzen lösen keine aggressive Regel aus |
| QS-03 | neue FTMS-Bike-Telemetrie | flags-basiertes Parsing und normalisierte Werte; Parser bleibt ohne reale Hardware unit-testbar |
| QS-04 | Sensor fällt während Workout aus | Gerät wird als nicht verfügbar markiert; Workout bleibt pausier-/abschließ-/abbrechbar |
| QS-05 | SIGTERM/SIGINT am Device Agent | BLE-Tasks und Verbindungen werden kontrolliert beendet; anschließender Start kann Geräte erneut verbinden |
| QS-06 | neues BLE-Gerät desselben fachlichen Typs | neuer Adapter/Parser kann ergänzt werden, ohne Workout-/Frontend-Domainlogik an Herstellerdetails zu koppeln |
| QS-07 | neue Telemetriegröße | expliziter Contract + Parser-/Service-/Frontend-Anpassung; unbekannte Werte bleiben optional |
| QS-08 | DB-Schema wird erweitert | Alembic-Migration reproduziert Schemaänderung auf frischer und bestehender DB; keine stillen fachlichen Datenreparaturen |
| QS-09 | fehlerhafte Telemetrienachricht | Nachricht wird validiert/verworfen bzw. als Fehlerzustand behandelt; API/Device Agent stürzen nicht wegen eines einzelnen Frames ab |
| QS-10 | Update auf neue Git-Revision | Fetch/optional Branch-Switch/Pull erfolgen kontrolliert; Provisionierung bricht bei Fehlern vor Service-Aktivierung sichtbar ab |
| QS-11 | `prepare.sh`/Migration schlägt fehl | abhängige Kernservices starten nicht gegen einen unvorbereiteten Runtime-Stand |
| QS-12 | Entwicklung und Produktion parallel | getrennte Ports/Prozesse dürfen sich nicht ungewollt beeinflussen; nur ein Device Agent greift auf dieselbe BLE-Hardware zu |
| QS-13 | Entwicklungs-/Produktivdaten | Test-/Dev-Datenbanken und Produktivdaten werden nicht vermischt |
| QS-14 | doppelter BLE-Zugriff | Betriebsregeln/Diagnose machen Konflikt sichtbar; keine Annahme paralleler exklusiver Geräteverbindungen |
| QS-15 | Workout-Abschluss | finaler persistierter Status wird serverseitig anhand fachlicher Regeln bestimmt |
| QS-16 | Frontend-Route oder direkter Reload | Caddy liefert SPA-Routen aus `frontend/dist`; `/api`, `/ws` und `/videos` werden vorher korrekt abgefangen |
| QS-17 | kein Internet / LLM deaktiviert | Kernbetrieb, Workout und deterministische Coaching-Texte bleiben verfügbar; Boot lädt keine Modelle nach |
| QS-18 | optionales TTS/LLM fehlerhaft oder langsam | sichtbares Coaching und Workout bleiben bedienbar; deterministischer Fallback greift |
| QS-19 | Video-Datei neu/entfernt | Scan ergänzt neue Dateien, reaktiviert wieder vorhandene Dateien und markiert fehlende Dateien inaktiv; fehlendes gesamtes Video-Root deaktiviert nicht pauschal alles |
| QS-20 | Caddy-Konfiguration ändert sich | Provisioning zeigt Diff/Nachfrage; `caddy validate` muss erfolgreich sein, bevor Caddy neu gestartet wird |

## 10.3 Prüfbarkeit

Die Qualitätsszenarien sollen soweit möglich durch Unit-/Integrations-/API-Tests, reproduzierbare Deployment-Schritte oder explizite Betriebschecks prüfbar bleiben. CI führt Backend- und Frontend-Checks aus; Dependabot prüft die npm-, pip- und GitHub-Actions-Abhängigkeiten regelmäßig gemäß `.github/dependabot.yml`.

---

# 11. Risiken und technische Schulden

## 11.1 Risiken

| ID | Thema | Risiko / Auswirkung | Gegenmaßnahme / nächster Schritt |
|---|---|---|---|
| R-01 | BLE/BlueZ | blockierter Adapter oder verlorene Verbindung | kontrollierter Shutdown, Reconnect, Diagnose über BlueZ/journalctl |
| R-02 | Doppelter Device Agent | zwei Prozesse konkurrieren um dieselbe Hardware | Dev-/Prod-Agent nicht parallel auf denselben Geräten betreiben |
| R-03 | DB-Migration/Rollback | Migration kann Rückkehr zu alter Revision erschweren | Backups/Rollback-Strategie weiter ausarbeiten; Migrationen explizit/testbar halten |
| R-04 | Update-Netzwerk | Dependency-/Modell-Download kann ausfallen | Downloads nur im Provisioning, Boot offline; bei Fehlern vor Restart abbrechen |
| R-05 | FTMS-Geräteunterschiede | Standardgeräte können Sonderfälle liefern | strikt flags-basierte Parser, aufgezeichnete Frames, Adaptergrenzen |
| R-06 | WebSocket-Reihenfolge/Reconnect | Zustände können kurz inkonsistent sein | robuste Merge-/Snapshot-/Reconnect-Tests |
| R-07 | Kiosk-Startreihenfolge | Browser kann vor Webserver/API bereit sein | Kiosk-Launcher wartet auf erfolgreiche HTTP-Antwort |
| R-08 | Kiosk-/Service-Rechte | unnötig breite Rechte erhöhen Schadenspotenzial | minimale Benutzer-/Gruppenrechte |
| R-09 | Mediengröße | Videos/Modelle erhöhen lokalen Speicherbedarf | Runtime-Daten getrennt von Quellcode behandeln, Speicherstrategie beobachten |
| R-10 | LLM-Faktentreue | kleines Modell kann Aussagen sprachlich verzerren | nur Formulierungsrolle, expliziter Kontext, deterministischer Fallback |
| R-11 | LLM-Latenz | CPU-Inferenz kann mehrere Sekunden dauern | optionale Nutzung; Kernentscheidungen niemals blockieren |
| R-12 | TTS-Queue/Prosodie | konkurrierende Events oder monotone Stimme | Priorität/Dedupe/Cancel-Policy; Presets/Voice evaluieren |
| R-13 | Adaptive Workouts | automatische Anpassung birgt Safety-Risiko | AdjustmentPolicy und Grenzen vor Automatisierung |
| R-14 | Video-Root | Mount/Verzeichnis kann zeitweise fehlen | kein Massendeaktivieren bei fehlendem Root; klare Diagnose |
| R-15 | Update nicht atomar | Build/Migration/Restart sind kein Blue/Green-Deployment | Backup, Health-Check, Aktivierungs-/Rollback-Konzept weiter härten |

## 11.2 Technische Schulden / offene Architekturthemen

- **Coaching-Priorisierung:** zentrale Event-Priorisierung/Deduplizierung für Safety, Runtime, Phasen, Milestones und Motivation.
- **Telemetry Publisher Layering:** Transporttypen dürfen nicht in Application/Domain einwandern; WebSocket-Adapter hinter Port halten.
- **Bike Control:** aktive FTMS-Steuerung bewusst getrennt von lesender Telemetrie; Lifecycle, Safety und manuelle Widerstandsverstellung vor Umsetzung klären.
- **WebSocket-Robustheit:** Reconnect, Snapshot-vs.-Live-Race und Zustandssynchronisation weiter explizit testen.
- **Appliance-Härtung:** Health-Checks, Watchdog, Backup und Rollback weiter ausbauen.
- **Dokumentation:** diese Datei ist die einzige kanonische arc42-Dokumentation; parallele `_old`-/Varianten-Dateien sollen nach Konsolidierung entfernt werden.

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
| Video-Root | über `HEALTH_COACH_VIDEO_DIR` konfiguriertes physisches Verzeichnis für Trainingsvideos |
| filePath | relativer Pfad eines Videos ab Video-Root; daraus wird im Frontend `/videos/...` erzeugt |
| Caddy | Produktions-Webserver für `frontend/dist` und Reverse Proxy zu FastAPI |
| Prepare | offline-fähige Runtime-Vorbereitung vor Service-Start |

---

# Anhang A – Funktionsliste

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
| Videos | Katalog-Synchronisation mit `data/videos` / konfiguriertem Video-Root | Vorhanden |
| Videos | Verwaltung aktiv/inaktiv, CRUD | Vorhanden |
| Videos | personenspezifische Auswahl nach Nutzung / zuletzt verwendet | Vorhanden |
| Videos | DB speichert relativen `file_path`, Frontend erzeugt `/videos/...` | Vorhanden |
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

# Anhang B – Feature-Roadmap

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

# Anhang C – Entwicklerleitfaden: Wo gehört neue Logik hin?

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
    -> Hook / Frontend-State-Service

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

# Anhang D – Pflegehinweise

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

# Anhang E – Verwandte Dokumentation

```text
arc42-digital-fitness-coach.md   -> diese kanonische Architekturreferenz
DEPLOYMENT.md                    -> Debian, systemd, Provisionierung und Betrieb
LOCAL-LLM.md                     -> lokale LLM-Runtime und Modellbetrieb
HOWTO-Entwicklungsumgebung.md    -> Entwicklungssetup
README.md                        -> Projekteinstieg
backend/docs/websockets.md       -> WebSocket-Verträge / technische Details
```

Die früheren arc42-Varianten können nach erfolgreicher Übernahme in Git archiviert oder entfernt werden, damit Architekturänderungen künftig an genau einer Stelle gepflegt werden.

---

# Anhang F – Wichtige Produktionspfade

```text
/opt/health-coach
    Git-Checkout / Anwendung

/opt/health-coach/backend/.venv
    Python-Virtual-Environment

/opt/health-coach/frontend/dist
    statischer Produktions-Build

/opt/health-coach/data/db/health-coach.db
    SQLite-Datenbank

/opt/health-coach/data/models/llm
    lokale LLM-Modelle

/opt/health-coach/data/models/piper
    Piper-Voice-Modell

/opt/health-coach/data/videos
    Standard-Video-Root

/etc/health-coach/backend.env
/etc/health-coach/llm.env
    produktive Runtime-Konfiguration

/etc/caddy/Caddyfile
    Frontend + Reverse Proxy

/etc/systemd/system/health-coach-*.service
    Produktionsservices
```

# Anhang G – Port- und Routingübersicht

| Port/Pfad | Komponente | Sichtbarkeit/Zweck |
|---|---|---|
| `:80` | Caddy | Browser-/Kiosk-Einstieg |
| `127.0.0.1:8000` | FastAPI | Produktions-API hinter Caddy |
| `127.0.0.1:8080` | llama-server | optionales lokales LLM |
| `/api/*` | Caddy → FastAPI | REST |
| `/ws/*` | Caddy → FastAPI | WebSockets |
| `/videos/*` | Caddy → FastAPI StaticFiles | Trainingsvideos |
| `/*` | Caddy → `frontend/dist` | React-SPA |

Entwicklungsports richten sich nach Makefile/Vite-Konfiguration und dürfen vom Produktionsbetrieb abweichen.

# Anhang H – Architekturregeln für zukünftige Erweiterungen

1. Domänenlogik importiert keine Infrastrukturframeworks.
2. Neue Hardware wird über Adapter integriert.
3. Gerätewerte werden vor Übergabe an Anwendung/UI normalisiert.
4. Unbekannte Messwerte bleiben optional; sie werden nicht erfunden.
5. Neue Datenbankschemata erhalten Alembic-Migrationen.
6. Neue Live-Telemetrie erhält explizite Contracts und Tests.
7. Test-/Dev-/Produktivdaten werden nicht unkontrolliert vermischt.
8. Produktionsprozesse sind über systemd/journald diagnostizierbar.
9. Hardware-Parser sind ohne reale Hardware unit-testbar.
10. Lesende Telemetrie und aktive Gerätesteuerung bleiben getrennte Fähigkeiten.
11. Frontend verwendet relative `/api`, `/ws` und `/videos`-Pfade.
12. Fehlende optionale Sensorik, TTS oder LLM darf den Workout-Kern nicht verhindern.
13. Generative Komponenten formulieren, entscheiden aber keine Safety-/Trainingsregeln.
14. Cross-Feature-Orchestrierung liegt im Composition Root.
15. Persistierte Medienpfade sind relative fachliche Pfade, keine Browser-URLs.

