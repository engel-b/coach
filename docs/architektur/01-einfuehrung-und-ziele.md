# 1. Einführung und Ziele

## 1.1 Aufgabenstellung

Der **Digital Fitness Coach** ist eine lokal betriebene Fitness- und Gesundheitsanwendung für mehrere Personen. Sie unterstützt den vollständigen Trainingsablauf von Personenauswahl und täglichem Check-in über Trainingsempfehlung und Workout-Durchführung bis zu Live-Telemetrie, Coaching, Sprachausgabe und Trainingshistorie.

Der funktionale Kern umfasst insbesondere:

- Personen und Profile mit Trainingsziel sowie Start-/Zielgewicht,
- tägliche Check-ins mit subjektiven und optionalen objektiven Gesundheitswerten,
- deterministische Pre-Workout-Empfehlungen,
- strukturierte Workouts mit Phasen und Runtime-Zuständen,
- Heart-Rate- und FTMS-Telemetrie über einen separaten Device Agent,
- Live-Coaching mit serverseitig erzeugten Coaching-Ereignissen,
- lokale TTS-Ausgabe über Piper,
- optionale lokale LLM-Formulierung mit deterministischem Fallback,
- einen lokalen Trainingsvideo-Katalog mit Synchronisation des Dateisystems,
- lokalen Appliance-/Kiosk-Betrieb unter Debian.

Das System soll nicht nur Messwerte anzeigen, sondern auf Basis von **Profil, Tagesform, Trainingshistorie, Workout-Phase und Live-Telemetrie** nachvollziehbar reagieren. Dabei gilt als wichtigstes Architekturprinzip:

```text
Deterministische Fachlogik entscheidet, WAS gilt und WAS passieren darf.
Optionale generative Komponenten dürfen höchstens beeinflussen, WIE etwas formuliert wird.
```

Das gilt insbesondere für Trainingsbelastung, Safety-Grenzen, Gewichtsinterpretation und Live-Coaching. Kernfunktionen sollen ohne Cloud-Abhängigkeit funktionieren. Optionale Komponenten wie HR-Sensor, TTS oder lokales LLM dürfen den Workout-Kern nicht unnötig blockieren.

## 1.2 Qualitätsziele

| Priorität | Ziel | Konsequenz |
|---:|---|---|
| 1 | Zuverlässigkeit | Datenintegrität, reproduzierbarer Start, saubere Migrationen, robuste Fallbacks |
| 2 | Nachvollziehbare Coaching-Logik | deterministische, testbare Regeln und explizite Gründe |
| 3 | Wartbarkeit | Package-by-Feature, klare Ports/Adapter, kleine Verantwortlichkeiten |
| 4 | Lokaler Betrieb | Kernfunktionen offline und ohne Cloud-Abhängigkeit |
| 5 | Bedienbarkeit | große klare UI, Coach-Feedback sichtbar und hörbar, Maus als vollständiger Bedienpfad |
| 6 | Erweiterbarkeit | LLM, TTS, Sensorik und weitere Coaching-Signale austauschbar ergänzbar |
| 7 | Verständlichkeit | Architekturdiagramme, ADRs, explizite Verträge und konsistente Entwicklerdokumentation |

## 1.3 Stakeholder

| Stakeholder | Interesse / Erwartung |
|---|---|
| Trainierende Personen | einfache Bedienung, gut lesbare Workout-Anzeige, nachvollziehbares Coaching und verlässliche Trainingsdaten |
| Betreiber / Administrator | automatischer Start, kontrollierte Updates, lokale Datenhaltung, nachvollziehbare Logs und einfache Wiederherstellung |
| Entwickler | klare Modulgrenzen, automatisierte Tests, reproduzierbarer Build und geringe Kopplung an Hardware/Frameworks |
| Geräteintegratoren | stabile Ports, normalisierte Telemetrie und testbare Parser/Adapter |
| Wartung / Support | Diagnose über systemd, journalctl, Health-Endpunkt und reproduzierbare Servicezustände |

## 1.4 Nicht-Ziele und Grenzen

Der Coach ist **kein medizinisches Diagnosesystem**. Er darf Trainings- und Gesundheitsdaten für Fitness-Coaching verwenden, soll aber keine Diagnosen oder unbelegten medizinischen Ursachen behaupten.

Gewichtsverlauf und Zielgewicht werden beschreibend ausgewertet. Ohne explizit konfigurierte Ziel-Abnahmerate wird aus einem langsameren oder schnelleren Gewichtsverlauf **keine automatische Intensivierung des Trainings** abgeleitet.

Aktive automatische Bike-Steuerung ist derzeit nicht Bestandteil des stabilen Kerns. Lesen von Telemetrie und aktive Gerätesteuerung bleiben getrennte Fähigkeiten.

---
