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

Produktionsprozesse schreiben auf stdout/stderr; systemd/journald sammelt die Ausgaben. Wichtige Diagnosepfade sind `systemctl status`, `journalctl -u ...`, der `/health`-Endpunkt sowie direkte Prüfungen der lokalen API-/LLM-Ports. Betriebsdetails stehen unter [Deployment und Betrieb](/betrieb/deployment).

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
