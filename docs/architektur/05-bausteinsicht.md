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

Die Workout-Zusammenfassung zeigt die dafür verwendeten aggregierten Hauptphasenwerte (durchschnittliche Herzfrequenz, Zielbereichsanteile, durchschnittliche Leistung und durchschnittliche Kadenz) zusammen mit der jeweiligen Stichprobenanzahl. Die Trainingsempfehlung formuliert die historische HR-/Power-Einordnung aus strukturierten API-Daten; das Frontend berechnet weder Zielbereiche noch Fitnessbewertungen selbst. Fehlende oder nicht ausreichend belastbare Historie wird nicht durch spekulative Aussagen ersetzt.

### LoadResponseContext

Der `LoadResponseContext` bündelt die bereits deterministisch abgeleiteten Signale aus Herzfrequenzverlauf, leistungsadjustierter HF-Reaktion, aggregierter Kadenz, aktuellem Readiness-Kontext und fachlichem Workout-Typ. Er liefert ausschließlich eine deskriptive Einordnung wie `stable`, `lower_hr_at_similar_load`, `higher_hr_at_similar_load`, `lower_load`, `higher_load`, `mixed` oder `insufficient_data`.

Die heutige Readiness wird dabei als separates Vorsichtssignal mitgeführt; sie verändert die historische Einordnung nicht rückwirkend. Umgekehrt darf ein günstiger historischer Verlauf keine automatische Intensitätssteigerung auslösen. Der Context ist damit eine gemeinsame fachliche Grundlage für UI und eine spätere adaptive Policy, aber selbst **keine** adaptive Trainingsentscheidung.

### AdaptiveWorkoutPolicy

Die `AdaptiveWorkoutPolicy` liest den `LoadResponseContext` zusammen mit Readiness, historischer Zielbereichsreaktion und dem bereits deterministisch gewählten Workout-Typ. Sie erzeugt ausschließlich strukturierte konservative Vorschläge: `keep_plan`, `reduce_duration`, `reduce_intensity`, `extend_warmup` oder `prefer_recovery`.

Jeder Vorschlag kennzeichnet zusätzlich, ob er im aktuellen Plan bereits berücksichtigt ist. Dauerbegrenzungen aus Readiness oder HF-Historie greifen weiterhin automatisch. Wenn heutige Vorsicht und mindestens drei vergleichbare Einheiten mit häufigem Überschreiten des Zielbereichs zusammenkommen, wird eine regenerative Einheit bevorzugt. Bei mindestens drei vergleichbaren Einheiten und höherem Puls bei ähnlicher Leistung verlängert die Planung das Warm-up um zwei Minuten zulasten der Hauptphase, sofern insgesamt mindestens 15 Minuten verfügbar sind. Zielpuls und Bike-Widerstand werden nicht automatisch verändert. Ein günstiger Verlauf (`lower_hr_at_similar_load`) löst keine Progression aus.

Die API liefert Aktion, stabile Reason Codes, den Reflektionsstatus und gegebenenfalls die empfohlene Dauer strukturiert an das Frontend. Die UI formuliert daraus transparent, was bereits angepasst wurde und was nur als konservativer Hinweis vorliegt.

Jede adaptive Entscheidung enthält zusätzlich einen `AdaptiveWorkoutDecisionContext`. Dieser Snapshot hält die für die Entscheidung verwendeten, bereits normalisierten Signale fest: Workout-Typ, verfügbare Trainingszeit, Readiness-Dauerlimit, Status und Dauerlimit der HF-Historie, `LoadResponseStatus`, Anzahl vergleichbarer Workouts und das heutige Readiness-Vorsichtssignal. API und Frontend verwenden diesen Snapshot für die Erklärung „Warum diese Empfehlung?“, statt die Entscheidung im Browser erneut herzuleiten.

Bei der Erzeugung einer Trainingsempfehlung wird die adaptive Entscheidung serverseitig als strukturierte Key/Value-Logzeile protokolliert. Geloggt werden Aktion, Reason-Codes und der Decision-Context, nicht jedoch Roh-HF- oder komplette Telemetrie-Zeitreihen. So lässt sich nach realen Einheiten nachvollziehen, welche deterministischen Eingangssignale zu einem Vorschlag geführt haben.

Beim Start eines Workouts werden Workout-Typ, historische Belastungsreaktion, Zahl vergleichbarer Einheiten, mediane Zielbereichsposition und mediane Leistung als Erwartung gespeichert. Die Summary vergleicht damit die Hauptphase: mindestens 30 HF- und 30 Leistungswerte sowie mindestens drei vergleichbare Einheiten sind für eine gemeinsame HF-/Leistungsbewertung erforderlich. Eine Abweichung der Zielbereichsposition um mindestens 15 Prozentpunkte gilt als höher/niedriger, Leistung innerhalb von ±10 % als vergleichbar. Fehlen Werte oder weicht die Leistung ab, wird die Übereinstimmung mit der Erwartung als nicht beurteilbar beziehungsweise nicht vergleichbar ausgewiesen. Bestehende Workouts ohne gespeicherte Erwartung bekommen keine rückwirkend konstruierte Auswertung.

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

Für Live-Hinweise berücksichtigt die Session neben der zusammenhängenden HF-Abweichungsdauer nur Bike-Daten, die höchstens 15 Sekunden vom HF-Sample entfernt liegen. Bei niedrigem Puls und fehlender oder geringer Kadenz (unter 50 rpm) wird keine Intensitätssteigerung empfohlen. Bei anhaltend hohem Puls und plausibler Leistung/Kadenz wird zu ruhigerem Tempo geraten; während des Warm-ups kann nach 45 Sekunden Überschreitung zum weiteren lockeren Einrollen geraten werden. Pausen, Phasenwechsel und Telemetrielücken setzen die relevante Historie zurück. Diese Hinweise verändern keine Phasengrenzen oder den FTMS-Widerstand.

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
