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
