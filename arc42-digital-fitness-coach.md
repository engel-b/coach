# Digital Fitness Coach – arc42-Architekturdokumentation

> Diese Dokumentation beschreibt den aktuell bekannten Stand. Geplante Funktionen sind ausdrücklich als geplant gekennzeichnet.

## 1. Einführung und Ziele

Der Digital Fitness Coach ist eine lokal betriebene Fitness- und Gesundheitsanwendung für mehrere Personen. Sie verbindet persönliche Profile, tägliche Check-ins, Gesundheitswerte, Trainingsempfehlungen, Workout-Durchführung, Sensorik und Fortschrittsdarstellung.

Primäre Bedienung ist die Maus; Sprache ist als zusätzlicher Interaktionskanal vorgesehen. Langfristiges Ziel ist eine lokale Appliance-/Kiosk-Anwendung.

### Qualitätsziele

| Priorität | Ziel | Konsequenz |
|---|---|---|
| 1 | Zuverlässigkeit | Datenintegrität, Migrationen, reproduzierbarer Start |
| 2 | Wartbarkeit | Package-by-Feature, klare Verantwortlichkeiten, Tests |
| 3 | Verständlichkeit | explizite Verträge, ADRs, Pseudografiken |
| 4 | Bedienbarkeit | klare große Bedienelemente, Maus zuerst |
| 5 | Lokaler Betrieb | Kernfunktionen ohne Cloud-Abhängigkeit |
| 6 | Erweiterbarkeit | Sensorik, Coach-Logik und Gesundheitswerte schrittweise ausbauen |

## 2. Randbedingungen

- Backend: Python, FastAPI, SQLAlchemy, Alembic
- Persistenz: SQLite
- Frontend: React + TypeScript
- lokaler Mehrpersonenbetrieb; derzeit vier initiale Personen
- Backend und Device Agent als getrennte Prozesse
- Entwicklung unter Linux und Windows
- Schemaänderungen über Alembic
- SQLite-Fremdschlüsselprüfung aktiviert
- optionale Gesundheitswerte bleiben `null`, wenn unbekannt

## 3. Kontextabgrenzung

```text
                         +----------------------+
                         | Trainierende Person  |
                         +----------+-----------+
                                    |
                              Maus / Sprache
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

Technischer Kontext:

```text
+---------------- Browser / Kiosk ----------------+
|              React / TypeScript                 |
+------------------------+------------------------+
                         | HTTP / WebSocket
                         v
               +---------+----------+
               | FastAPI API        |
               | Composition Root   |
               +----+----------+----+
                    |          |
                    v          v
              +-----+----+  +--+----------------+
              | SQLite   |  | Device Agent /    |
              | SQLAlchemy| | Bluetooth Adapter |
              +----------+  +---------+---------+
                                      |
                                      v
                               FTMS / Heart Rate
```

## 4. Lösungsstrategie

1. Package-by-Feature statt globaler technischer Schichten.
2. Domänenmodelle ohne Infrastrukturwissen.
3. `service/` für Use Cases und Anwendungslogik.
4. API-Verträge getrennt von Domänenobjekten.
5. Repository-Abstraktionen für Persistenz.
6. SQLAlchemy + Alembic für SQLite.
7. Adapter für Hardware und technische Integrationen.
8. React-Komponenten für klar abgegrenzte Benutzerflüsse.
9. Kleine, testbare und deploybare Änderungsschritte.

## 5. Bausteinsicht

```text
backend/
+-- apps/
|   +-- api/
|   |   +-- main.py
|   |   +-- wiring.py
|   |   +-- routers/
|   +-- device_agent/
|       +-- main.py
|       +-- lifecycle.py
+-- features/
|   +-- person/
|   +-- check_in/
|   +-- training/
|   +-- workout/
|   +-- telemetry/
+-- adapters/
|   +-- persistence/
|       +-- database.py
+-- alembic/
+-- tests/
+-- scripts/
```

Feature-interne Struktur:

```text
feature/
+-- domain/          fachliche Modelle und Interfaces
+-- service/         Use Cases / Anwendungslogik
+-- api/
|   +-- contracts/   HTTP-Verträge
|   +-- router.py
+-- persistence/     SQLAlchemy / Repositories
+-- adapters/        falls feature-spezifisch erforderlich
```

### Features

**person:** Person, Anzeigename, Profil, Geburtsdatum, Größe, Trainingsziel, optionale maximale Herzfrequenz, Start- und Zielgewicht. Person und Profil sind 1:1 getrennt persistiert.

**check_in:** Energie, Erholung, Muskelkater, Stress, verfügbare Trainingszeit, aktuelles Gewicht, Schlaf, Schritte und Historie.

**training:** Fachliche Trainingskonzepte und Verträge für Empfehlungen.

**workout:** Workout-Lebenszyklus, Status, Dauer, Distanz, Videozustand, Phasen, Historie und Summary.

**telemetry:** Geräte-/Sensordaten; FTMS und Heart Rate liegen als Bluetooth-Adapter unter dem Feature.

Frontend:

```text
React App
+-- Personenauswahl / Profil
+-- Check-in Wizard
|   +-- Tagesform
|   +-- Trainingszeit
|   +-- Gewicht / Schlaf / Schritte
+-- Dashboard
|   +-- Gewichtsverlauf
|   +-- Coach
|   +-- Badges
|   +-- Workout-Historie
+-- Workout
|   +-- Durchführung / Telemetrie / Video
|   +-- Zusammenfassung
+-- API-Clients
```

## 6. Laufzeitsicht

Check-in:

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

Dashboard:

```text
PersonDashboard
      |
      +------> Profil
      +------> letzter Check-in
      +------> Check-in-Historie
      +------> Workout-Historie
      |
      v
+---------------------------+
| React Dashboard-Zustand   |
+-------------+-------------+
              |
      +-------+--------+----------------+
      v                v                v
 Gewichts-          Coach-          Workout-
 verlauf            Bereich         Historie
```

Workout:

```text
Person
  |
  v
Frontend ---------> FastAPI ---------> WorkoutService
  |                                      |
  |                                      v
  |                                   SQLite
  |
  +--------------> Device Agent ------> Bluetooth
                                      FTMS / HR
```

Entwicklungsstart:

```text
                  make dev
                     |
        +------------+-------------+
        |            |             |
        v            v             v
  make backend  make device-  make frontend
                  agent
        |            |             |
        v            v             v
     FastAPI     Device Agent    React Dev Server
```

## 7. Verteilungssicht

Entwicklung:

```text
+---------------- Entwickler-PC ----------------+
| React Dev Server                              |
| FastAPI Backend                               |
| Device Agent                                  |
| SQLite DB                                     |
| Bluetooth Hardware (optional)                 |
+-----------------------------------------------+
```

Zielbild Appliance:

```text
+---------------- Fitness-Coach-Gerät ----------------+
| +---------------- Kiosk UI -----------------------+ |
| | React Frontend                                  | |
| +----------------------+--------------------------+ |
| +----------------------+--------------------------+ |
| | FastAPI Backend                                 | |
| +----------------------+--------------------------+ |
| +------------+   +-----+------+   +-------------+ |
| | SQLite DB  |   | Device     |   | lokale      | |
| |            |   | Agent      |   | Medien      | |
| +------------+   +-----+------+   +-------------+ |
+------------------------|----------------------------+
                         v
                  Bluetooth-Geräte
```

## 8. Querschnittliche Konzepte

### Persistenz und Datenintegrität

SQLite-Fremdschlüssel werden erzwungen. Migrationen müssen Bestandsdaten und abhängige Tabellen berücksichtigen.

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

Vor referenziellen Schemaänderungen werden Orphans geprüft. Migrationen dürfen fachliche Produktivdaten nicht still löschen oder erfinden.

### Fehlende Messwerte

```text
keine Eingabe  ---> null
unbekannt      -X-> 0
```

### API-Verträge

HTTP-Verträge sind von Domänenmodellen getrennt. Das Frontend verwendet camelCase.

### Teststrategie

```text
+------------------+
| Domain / Service |
| Unit Tests       |
+--------+---------+
         v
+--------+---------+
| Repository / API |
| Integration      |
+--------+---------+
         v
+--------+---------+
| Alembic-migrierte|
| SQLite Test-DB   |
+------------------+
```

Migrationstests mit Fremdschlüsseln müssen relevante referenzierte Bestandsdaten enthalten; eine ausschließlich leere Testdatenbank reicht nicht.

### Diagramme in der Dokumentation

Architekturdiagramme werden **direkt als Pseudografik in Markdown** gepflegt. Sie bleiben damit im Git-Diff, Terminal und einfachen Markdown-Viewern lesbar.

Beispiel:

```text
+-------------+       HTTP       +-------------+
| Frontend    | ----------------> | Backend     |
+-------------+                   +-------------+
```

Konventionen:

```text
+-------------+     Komponente/System
| Komponente  |
+-------------+

------>             gerichteter Aufruf/Datenfluss
<----->             bidirektionale Kommunikation
+----<               1:n-Beziehung, wenn eindeutig
[optional]           optionaler Bestandteil
```

Diagramme zeigen relevante Grenzen und Verantwortlichkeiten, nicht jede Klasse. Zu breite Diagramme werden vertikal aufgebaut. Screenshots ersetzen keine Architekturdiagramme. Mermaid/PlantUML können später ergänzen; die Pseudografik bleibt die portable Referenz.

## 9. Architekturentscheidungen (ADRs)

### ADR-001 – Package-by-Feature
**Status:** Akzeptiert  
Fachliche Module liegen unter `features/`; technische Schichten innerhalb des Features. Gemeinsame Infrastruktur bleibt außerhalb.

### ADR-002 – Service-Schicht heißt `service/`
**Status:** Akzeptiert  
Use Cases und Anwendungslogik liegen einheitlich unter `service/`; es gibt keine parallele `application/`-Struktur.

### ADR-003 – SQLite als lokale Persistenz
**Status:** Akzeptiert  
SQLite unterstützt den lokalen Appliance-Charakter. SQLite-spezifisches FK- und DDL-Verhalten muss explizit getestet werden.

### ADR-004 – SQLAlchemy und Alembic
**Status:** Akzeptiert  
SQLAlchemy übernimmt Datenzugriff, Alembic versionierte Schemaänderungen.

### ADR-005 – SQLite-Fremdschlüssel werden erzwungen
**Status:** Akzeptiert  
SQLite-Verbindungen verwenden `PRAGMA foreign_keys=ON`. Batch-Migrationen müssen abhängige Tabellen berücksichtigen.

### ADR-006 – Migrationen erfinden oder löschen keine fachlichen Daten still
**Status:** Akzeptiert  
Nicht eindeutig reparierbare Inkonsistenzen führen zum Abbruch. Datenkorrekturen bleiben explizit und nachvollziehbar.

### ADR-007 – Person und PersonProfile getrennt
**Status:** Akzeptiert

```text
+--------+       1 : 1       +----------------+
| person | ----------------- | person_profile |
+--------+                    +----------------+
```

Stabile Identität bleibt von erweiterbaren Profildaten getrennt.

### ADR-008 – Gesundheitswerte über Check-ins historisieren
**Status:** Akzeptiert

```text
PersonProfile              CheckIn-Historie
+----------------+         +-------------------+
| startWeightKg  |         | currentWeightKg   |
| targetWeightKg |         | sleepHours        |
+----------------+         | steps             |
                           +-------------------+
```

### ADR-009 – Fehlende Gesundheitswerte als `null`
**Status:** Akzeptiert  
Nicht eingegebene Werte werden als `null` übertragen und gespeichert.

### ADR-010 – Telemetrie-Hardware über Adapter
**Status:** Akzeptiert

```text
Telemetry Domain
       ^
       |
Telemetry Service
       ^
       |
Bluetooth Adapter
  +----+----+
  |         |
 FTMS      HR
```

### ADR-011 – API und Device Agent als getrennte Prozesse
**Status:** Akzeptiert  
HTTP-Anwendung und Hardware-Lebenszyklus bleiben getrennt. Entwicklung/Deployment benötigen kontrolliertes Prozessmanagement.

### ADR-012 – Gewichtsdiagramm leichtgewichtig ohne Chart-Bibliothek
**Status:** Akzeptiert  
SVG zeichnet Kurve und Referenzlinien; HTML/CSS übernimmt Elemente, die durch `preserveAspectRatio="none"` nicht verzerrt werden dürfen.

```text
kg
| Start ---------------------------------
|             o
|          o-----o
|       o           o
| Ziel  ---------------------------------
+---------------------------------------> Zeit
```

Bei deutlich wachsender Diagrammkomplexität wird die Entscheidung neu bewertet.

### ADR-013 – Architekturdiagramme als Markdown-Pseudografik
**Status:** Akzeptiert  
Pseudografiken in `text`-Codeblöcken sind die portable Referenz der Architekturdokumentation.

### ADR-014 – UI zunächst Maus, Sprache als Erweiterung
**Status:** Akzeptiert  
Kernpfade funktionieren vollständig per Maus. Sprache ergänzt sie später und darf Kernfunktionen nicht blockieren.

## 10. Qualitätsanforderungen

- Referenzverletzungen werden durch DB-Constraints sichtbar.
- Fachliche Änderungen sollen überwiegend innerhalb eines Features bleiben.
- Große klare Klickziele und direkt editierbare Zahlenwerte.
- Fehlende Werte werden als `–` statt als erfundene Messung dargestellt.
- Optionale Sensorik darf die Kernanwendung nicht unbenutzbar machen.
- Ergänzende Dashboard-Daten dürfen fehlertolerant geladen werden, wenn der Kernscreen sinnvoll bleibt.

## 11. Risiken und technische Schulden

| Thema | Risiko / Schuld | Nächster Schritt |
|---|---|---|
| Windows `make dev` | Mehrprozessstart/Shutdown noch nicht endgültig robust | Prozessmanagement vereinheitlichen |
| Migrationstests | leere DB deckt FK-Rebuild-Probleme nicht ab | Tests mit referenzierten Bestandsdaten |
| Gewichtsdiagramm | X-Punkte aktuell nach Index | echte Zeitachse |
| Dashboard Coach | Logik noch einfach/deterministisch | fachlichen Service anbinden |
| Badges | aus begrenzt geladener Historie abgeleitet | persistente Achievement-Logik |
| Workout-Historie | generische Darstellung | Metadaten ergänzen |
| Sprache | noch kein vollständiger Bedienpfad | Voice-Konzept/Adapter |
| Kiosk | bisher Zielbild | Autostart, Recovery, Fullscreen, Watchdog |

## 12. Glossar

| Begriff | Bedeutung |
|---|---|
| Check-in | Tagesform plus optionale Gesundheitswerte |
| Device Agent | separater Prozess für Hardware/Bluetooth |
| FTMS | Bluetooth Fitness Machine Service |
| HR | Heart Rate |
| Workout Phase | Teilabschnitt eines Workouts |
| Appliance | lokal betriebenes eigenständiges Coach-Gerät |
| Orphan | Datensatz mit ungültiger Elternreferenz |
| ADR | Architecture Decision Record |

# Funktionsliste

Legende: **Vorhanden**, **Teilweise**, **Geplant**.

| Bereich | Funktion | Status |
|---|---|---|
| Personen | mehrere Personen / stabile IDs | Vorhanden |
| Profil | Basisdaten und Trainingsziel | Vorhanden |
| Profil | Start-/Zielgewicht, optionale max. HF | Vorhanden |
| Check-in | Energie, Erholung, Muskelkater, Stress | Vorhanden |
| Check-in | verfügbare Trainingszeit | Vorhanden |
| Check-in | Gewicht, Schlaf, Schritte | Vorhanden |
| Check-in | Historie | Vorhanden |
| Dashboard | aktuelles Gewicht und Veränderung | Vorhanden |
| Dashboard | Gewichtsverlauf und kg-Skala | Vorhanden |
| Dashboard | Start-/Ziel-Referenzlinien | Vorhanden |
| Dashboard | Coach-Bereich | Teilweise |
| Dashboard | Badges | Teilweise |
| Dashboard | Workout-Historie | Vorhanden |
| Workout | Lebenszyklus, Dauer, Distanz | Vorhanden |
| Workout | Videozustand und Phasen | Vorhanden |
| Workout | Summary | Vorhanden / UX-Ausbau |
| Telemetrie | FTMS-/Heart-Rate-Architektur | Vorhanden |
| Datenbank | Alembic, FK-Enforcement, Referenz-Audit | Vorhanden |
| Betrieb | Windows-Entwicklungsstart | Teilweise |
| Bedienung | Maus | Vorhanden |
| Bedienung | Sprache | Geplant |
| Betrieb | Kiosk-/Appliance-Modus | Geplant |
| Gesundheit | weitere Körpermaße | Geplant |
| Dashboard | echte Zeitachse / Zeitraumwahl | Geplant |

# Feature-Roadmap

## Phase 1 – Stabiler Gesundheits- und Fortschrittskern

```text
Profil
  |
  v
Check-in ------> Gesundheits-Historie
  |                    |
  +--------------------+
             |
             v
         Dashboard
```

- echte Zeitachse im Gewichtsdiagramm
- Zeitraumwahl, z. B. 30/90 Tage/alle
- Veränderung passend zum Zeitraum
- letzten tatsächlich vorhandenen Gewichtswert robust bestimmen
- Migrationstests mit realistischen FK-Beziehungen
- Windows-`make dev` mit sauberem Start/Shutdown
- Dashboard-Fehler- und Empty-States finalisieren

**Done:** Check-ins erscheinen zuverlässig in Historie/Dashboard; Migrationen sind mit referenzierten Bestandsdaten getestet.

## Phase 2 – Coach und Trainingsentscheidung

```text
Profil --------+
Check-in ------+
Historie ------+----> Coach-Regeln ----> Empfehlung
Workouts ------+                         |
                                         v
                                      Training
```

- Coach-Logik aus UI-Texten in fachliche Services
- Intensität und Dauer nachvollziehbar empfehlen
- Gründe anzeigen
- Erholung, Stress, Muskelkater, Zeit und Trainingsziel berücksichtigen
- Empfehlung mit Workout-Auswahl verbinden

## Phase 3 – Workout-Erlebnis und Telemetrie

```text
Empfehlung
    |
    v
 Workout <------ FTMS / Heart Rate
    |
    +------> Live-Telemetrie
    |
    v
 Summary ------> Historie
```

- Summary-UX vervollständigen
- Telemetrie mit Workout-Lebenszyklus verbinden
- Verbindungsabbrüche/Wiederverbindung
- relevante Live-Werte
- Workout-/Video-Metadaten in Historie
- Abbruch und Abschluss fachlich sauber auswerten

## Phase 4 – Langfristiger Gesundheitsverlauf

```text
Check-ins ------+
Workouts -------+
Körpermaße -----+----> Verlauf / Trends ----> Coach
Profilziele ----+
```

- optionale Körpermaße wie Taille/Brust
- letzter Messzeitpunkt
- Trends für Schlaf, Schritte und Training
- langfristige Zielerreichung
- Badges auf vollständiger Historie
- Aggregation ohne erfundene Werte

## Phase 5 – Sprache und Coach-Interaktion

```text
                  +---- Maus -----------+
                  |                     |
Person -----------+                     +----> Use Case
                  |                     |
                  +---- Sprache --------+
```

- Sprache als zusätzlicher Interaktionskanal
- Person/Kontext eindeutig halten
- Check-in sprachgeführt
- sinnvolle Workout-Sprachaktionen
- optionale Sprachausgabe
- sichtbare Mausalternative für zentrale Aktionen

## Phase 6 – Appliance-/Kiosk-Betrieb

```text
Power On
   |
   v
Supervisor
   |
   +----> SQLite vorbereiten / migrieren
   +----> Backend
   +----> Device Agent
   +----> Kiosk Frontend
   |
   v
Health Coach bereit
```

- Autostart
- Kiosk/Fullscreen
- kontrollierter Mehrprozessstart
- Health Checks und Recovery
- lokale Backups
- Update/Rollback
- Wartungsmodus
- Betrieb ohne Entwicklungswerkzeuge

# Pflegehinweise

1. Relevante Architekturentscheidungen erhalten einen ADR.
2. Ersetzte ADRs werden als `Ersetzt` markiert und verweisen auf den Nachfolger.
3. Neue System-/Datenflüsse werden direkt als Pseudografik dokumentiert.
4. Implementierte Roadmap-Punkte aktualisieren die Funktionsliste.
5. Geplante Funktionen werden nicht als vorhanden dokumentiert.
6. DB-/Deploymentänderungen werden auch in Persistenz, Laufzeitsicht und Risiken geprüft.
7. Diagramme zeigen Architektur und Verantwortlichkeiten, nicht unnötig jede Klasse.
