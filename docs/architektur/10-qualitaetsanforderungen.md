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
