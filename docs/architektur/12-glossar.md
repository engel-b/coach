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
