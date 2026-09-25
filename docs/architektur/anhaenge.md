# Anhänge

Ergänzende Listen und historische Planung zur [arc42-Architektur](/architektur/). Der aktuelle Implementierungsstand steht im [Überblick](/architektur/).

## Anhang A – Funktionsliste

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
| Coaching | historische HR-/Leistungs-Korrelation aus aggregierten Hauptphasenwerten | Vorhanden |
| Workout | vorsichtige adaptive Plananpassung und Live-Hinweise | Vorhanden; automatische Widerstandssteuerung nicht vorgesehen |
| Sprache | Spracheingabe | Geplant |
| Betrieb | Rollback/Watchdog/Health-Härtung | Geplant |

---

## Anhang B – Feature-Roadmap

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

- Kadenz und Leistung zusätzlich **live** als Coaching-Signale nutzen; die historische deskriptive Auswertung ist bereits vorhanden;
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

Vorsichtige Plananpassungen und deskriptive Live-Hinweise sind umgesetzt. Weitere Automatisierung, insbesondere aktive Widerstandssteuerung, setzt zusätzliche Safety- und Begrenzungsregeln voraus.

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

## Anhang C – Entwicklerleitfaden: Wo gehört neue Logik hin?

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

## Anhang D – Pflegehinweise

1. **Diese Datei ist die einzige kanonische arc42-Dokumentation.** Neue Varianten mit Suffixen wie `-aktuell`, `-tts` oder `-llm-plan` sollen nicht mehr parallel gepflegt werden.
2. Implementierte Änderungen aktualisieren mindestens Statusübersicht, Funktionsliste und betroffene Laufzeit-/Bausteinsicht.
3. Relevante Architekturentscheidungen erhalten oder aktualisieren einen ADR.
4. Ersetzte Entscheidungen werden als ersetzt markiert; Historie wird nicht still überschrieben.
5. Geplante Funktionen werden nicht als vorhanden dokumentiert.
6. Deployment-Details stehen im [Betriebsleitfaden](/betrieb/deployment); die arc42-Kapitel beschreiben die Architektur.
7. Neue Cross-Feature-Abhängigkeiten werden bevorzugt im Composition Root orchestriert.
8. Neue Coaching-Regeln benötigen Unit-Tests und nachvollziehbare Reason Codes.
9. Optionale Komponenten müssen ein definiertes Degradationsverhalten besitzen.
10. Sicherheit, Trainingsentscheidung und generative Formulierung bleiben getrennte Verantwortlichkeiten.

---

## Anhang E – Verwandte Dokumentation

- [Architekturüberblick](/architektur/) – arc42-Kapitel 1–12
- [Deployment und Betrieb](/betrieb/deployment) – Debian, systemd und Provisionierung
- [Lokales LLM](/betrieb/lokales-llm) – Runtime und Modellbetrieb
- [Entwicklungsumgebung](/entwicklung/einrichten) – Windows und Linux
- [WebSocket-Schnittstellen](/schnittstellen/websockets) – technische Verträge

---

## Anhang F – Wichtige Produktionspfade

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

/opt/health-coach/data/models/piper-tts
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

## Anhang G – Port- und Routingübersicht

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

## Anhang H – Architekturregeln für zukünftige Erweiterungen

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
