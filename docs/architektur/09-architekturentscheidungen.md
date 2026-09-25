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

## ADR-018c – HR-/Power-Korrelation bleibt deskriptiv
**Status:** Akzeptiert

Für historische Belastungsreaktionen dürfen Herzfrequenz und aggregierte FTMS-Leistung gemeinsam betrachtet werden. Nur bei ausreichend belegten, fachlich vergleichbaren Workouts wird beschrieben, ob sich die relative Herzfrequenz bei ähnlicher oder deutlich veränderter Bike-Leistung verschoben hat. Kadenz und Leistung bleiben optionale Sensorsignale. Aus einer günstigeren historischen Relation folgt keine automatische Erhöhung von Zielpuls, Dauer, Widerstand oder sonstiger Trainingsintensität.


## ADR-018d – Belastungsreaktion zunächst nur deskriptiv zusammenführen

**Entscheidung:** Herzfrequenztrend, historische Bike-Leistung, aggregierte Kadenz, heutige Readiness und Workout-Typ werden in einem `LoadResponseContext` zusammengeführt. Dieser Context darf Trainingsparameter nicht selbst verändern.

**Begründung:** Die Signale sind gemeinsam aussagekräftiger als isoliert, reichen aber noch nicht für eine belastbare automatische Anpassung von Dauer, Zielpuls oder Widerstand. Die Trennung schafft eine stabile, testbare Zwischenstufe vor späteren adaptiven Policies.

**Konsequenz:** Eine spätere automatische Anpassung benötigt eine eigene deterministische Policy mit expliziten Regeln und Safety-Grenzen; der `LoadResponseContext` bleibt beobachtend.

## ADR-018e – AdaptiveWorkoutPolicy bleibt konservativ und transparent

**Entscheidung:** Eine eigene `AdaptiveWorkoutPolicy` darf aus `LoadResponseContext`, Readiness und historischer HF-Reaktion deterministische Anpassungsvorschläge ableiten. Sie darf keine automatische Progression aus einem günstigen Verlauf erzeugen.

**Begründung:** Historische HF-/Bike-Signale sind nützlich, aber nicht ausreichend, um Zielpuls, Widerstand oder Trainingslast automatisch zu erhöhen. Konservative Vorschläge müssen von Safety-Grenzen und Gerätesteuerung getrennt bleiben.

**Konsequenz:** Bereits vorhandene Dauerbegrenzungen können als im Plan reflektiert ausgewiesen werden. Intensitätsreduktion und längeres Warm-up bleiben zunächst advisory-only. Eine spätere automatische Anwendung benötigt einen eigenen Use Case mit expliziten Grenzen, Tests und Safety-Regeln.

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
