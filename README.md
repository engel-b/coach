# Health Coach

Local-first Fitness- und Gesundheits-Coach für wenige Personen. Die Anwendung kombiniert Check-ins, nachvollziehbare Trainingsempfehlungen, strukturierte Workouts, BLE-Telemetrie, Live-Coaching und lokale Piper-Sprachausgabe. Ein lokales LLM kann optional Texte formulieren; Trainingsentscheidungen bleiben deterministisch.

## Projektdokumentation

Die VitePress-Projektseite liegt unter [`docs/`](docs/index.md) und bietet Suche und Navigation:

- [Architektur nach arc42](docs/architektur/index.md)
- [Entwicklungsumgebung einrichten](docs/entwicklung/einrichten.md)
- [Deployment und Betrieb](docs/betrieb/deployment.md)
- [Lokales LLM](docs/betrieb/lokales-llm.md)
- [WebSocket-Schnittstellen](docs/schnittstellen/websockets.md)

Lokal ansehen (Node.js 24 gemäß `.nvmrc`, im Repository-Root):

```bash
make docs-dev
```

Anschließend **http://127.0.0.1:5174/** im Browser öffnen. Der Befehl installiert fehlende Dokumentations-Abhängigkeiten automatisch.

Die statische Projektseite wird mit `make docs-build` gebaut; sie wird separat vom React-Frontend unter `frontend/` bereitgestellt. [Dokumentation bearbeiten](docs/entwicklung/dokumentation.md).

Nach Aktivierung von **GitHub Actions** unter **Settings → Pages** veröffentlicht der [Pages-Workflow](.github/workflows/docs-pages.yml) Änderungen an der Dokumentation vom Standardbranch automatisch. Für `engel-b/coach` liegt die Site dann unter `https://engel-b.github.io/coach/`.

## Entwicklung

Backend und Frontend installieren, dann im Repository-Root `make dev` starten. Die vollständigen Schritte und Windows-/Linux-Befehle stehen unter [Entwicklungsumgebung einrichten](docs/entwicklung/einrichten.md). Tests: `make check`.

Für Produktionsupdates auf der Appliance: `./deploy/provision.sh` gemäß [Deployment und Betrieb](docs/betrieb/deployment.md). Der normale Boot-Pfad lädt keine Abhängigkeiten oder Modelle herunter.
