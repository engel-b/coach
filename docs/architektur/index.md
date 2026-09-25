# Architektur nach arc42

> **Kanonische Dokumentation**
> Sie beschreibt den **implementierten Stand**, ausdrücklich gekennzeichnete **optionale/experimentelle Bausteine** sowie die **geplante Weiterentwicklung**. Deployment-Details werden ergänzend in [Deployment und Betrieb](/betrieb/deployment) gepflegt.

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
| Adaptive Workout-Anpassung | ✅ Vorsichtig umgesetzt | erklärbare Empfehlung, begrenzte Plananpassungen und Live-Hinweise; keine automatische Widerstandssteuerung |
| Spracheingabe | 🧭 Geplant | Sprache als zusätzlicher Interaktionskanal, nicht als einziger Bedienpfad |

---

Die zwölf Kapitel und [Anhänge](/architektur/anhaenge) stammen aus der bisherigen arc42-Dokumentation und sind hier als einzelne Seiten durchsuchbar. Praktische Anleitungen stehen unter [Betrieb](/betrieb/deployment) und [Entwicklung](/entwicklung/einrichten).
