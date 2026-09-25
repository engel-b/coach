# 2. Randbedingungen

## 2.1 Technische Randbedingungen

- Backend: Python, FastAPI, Pydantic, SQLAlchemy, Alembic
- Persistenz: SQLite
- Frontend: React + TypeScript + Vite
- Tests: pytest / mypy / Ruff im Backend, Vitest / ESLint im Frontend
- Device Agent: separater Python-Prozess auf Basis von `asyncio`/Bleak
- Bluetooth: FTMS und Heart Rate
- TTS: lokale Piper-Engine hinter einem Port/Adapter
- Lokales LLM: OpenAI-kompatible HTTP-Schnittstelle, aktuell über `llama-server`
- Produktion: Debian, systemd und Caddy
- Entwicklung: Windows und Linux
- Node.js: 24 LTS; Projektuntergrenze `>=24.15.0 <25`

Zielhardware der aktuellen Appliance ist ein Lenovo ThinkCentre M900z mit Intel Core i3-6100 und 16 GB RAM. Eine dedizierte GPU wird weder für den Kernbetrieb noch für TTS vorausgesetzt.

## 2.2 Organisatorische und betriebliche Randbedingungen

Die Architektur wird inkrementell weiterentwickelt. Dokumentation, Build, Tests, Migrationen und Deployment sind Bestandteil des Produkts und werden gemeinsam mit dem Code versioniert.

Die Produktionsinstallation ist ein Git-Checkout unter `/opt/health-coach`. Laufzeitdaten liegen innerhalb des dafür vorgesehenen `data/`-Baums und werden nicht als Quellcode behandelt:

```text
/opt/health-coach/data/
├── db/
├── models/
│   ├── llm/
│   └── piper/
└── videos/
```

Die produktiven Prozesse laufen getrennt:

```text
health-coach-prepare.service
health-coach-api.service
health-coach-device-agent.service
health-coach-llm.service       [optional]
Caddy                           [statische UI + Reverse Proxy]
Chromium-Kiosk                  [grafische Benutzersitzung]
```

`provision.sh` ist der explizite Update-/Deployment-Pfad und darf Netzwerkzugriff, Dependency-Installation, Builds und Modell-Provisionierung durchführen. `prepare.sh` ist die offline-fähige Boot-Vorbereitung und beschränkt sich auf lokale Runtime-Prüfung und Datenbankmigrationen.

## 2.3 Konventionen

- Backend-interne Python-Namen verwenden `snake_case`.
- JSON-Verträge und TypeScript verwenden `camelCase`.
- Beispiel: `file_path` im Backend entspricht `filePath` im API-/Frontend-Vertrag.
- Domänenobjekte importieren keine FastAPI-, SQLAlchemy-, Bleak- oder React-Typen.
- Datenbankschemaänderungen erfolgen ausschließlich über Alembic-Migrationen.
- Fehlende fachliche oder sensorische Werte bleiben optional/`null`; sie werden nicht als `0` oder durch Schätzwerte erfunden.
- Cross-Feature-Orchestrierung gehört in den App-/Composition-Root.
- Frontend-Code verwendet relative `/api`, `/ws` und `/videos`-Pfade und kennt Produktionsports nicht.
- Neue Hardware wird über Adapter integriert und vor Übergabe an Domain/UI normalisiert.

## 2.4 Fachliche Randbedingungen

- ein fehlender HR-Sensor verhindert kein Workout;
- Coaching-Entscheidungen werden serverseitig erzeugt;
- Workout-Status wird serverseitig final bestimmt;
- Browser und Backend kommunizieren über explizite HTTP-/WebSocket-Verträge;
- LLM und TTS sind austauschbare technische Komponenten und keine fachlichen Entscheidungsträger;
- Workout-Videos werden in der Datenbank mit einem Pfad relativ zum konfigurierten Video-Root gespeichert; die Browser-URL wird daraus abgeleitet.

---
