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
| R-13 | Adaptive Workouts | automatische Anpassung birgt Safety-Risiko | bestehende vorsichtige Anpassungen anhand echter Einheiten prüfen; vor weiteren Eingriffen explizite Grenzen und Safety-Regeln festlegen |
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
