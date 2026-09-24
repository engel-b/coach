# Health Coach

Local-first digital fitness and health coach for a small number of users. The application combines health/readiness check-ins, deterministic training recommendations, structured workouts, live BLE telemetry, live coaching, local TTS, an optional local LLM and a local training-video catalog.

[![CI](https://github.com/engel-b/coach/actions/workflows/ci.yml/badge.svg)](https://github.com/engel-b/coach/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![Node](https://img.shields.io/badge/node-24_LTS-green)
![License](https://img.shields.io/badge/license-private-lightgrey)

## Current capabilities

- multiple persons and profiles
- daily check-ins with weight, sleep, steps and subjective readiness signals
- deterministic pre-workout recommendation with structured reasons
- workout phases and runtime states (`running`, `paused`, `finish_window`, `overtime`)
- Heart Rate and FTMS telemetry through a separate Device Agent
- server-side live coaching via `/ws/coaching`
- local Piper TTS
- optional local OpenAI-compatible LLM with deterministic fallback
- training-video catalog synchronized with a configurable local video directory
- SQLite persistence with SQLAlchemy and Alembic
- Debian appliance deployment with systemd, Caddy and Chromium kiosk mode

The central architecture rule is:

```text
Deterministic domain logic decides WHAT is true and WHAT may happen.
Optional generative components may only influence HOW it is worded.
```

## Repository layout

```text
health-coach/
├── backend/
├── frontend/
├── data/
│   ├── db/
│   ├── models/
│   │   ├── llm/
│   │   └── piper/
│   └── videos/
├── deploy/
├── Makefile
├── README.md
├── arc42-digital-fitness-coach.md
├── DEPLOYMENT.md
├── HOWTO-Entwicklungsumgebung.md
└── LOCAL-LLM.md
```

`data/` contains local runtime data and assets. Video records store a path relative to the configured video root; browser URLs are built as `/videos/<filePath>`.

## Requirements

- Python 3.11+
- Node.js 24 LTS (`>=24.15.0 <25`; tested version in `.nvmrc`)
- npm
- Git
- GNU Make
- Linux/BlueZ for real BLE device integration

For the detailed development setup, see `HOWTO-Entwicklungsumgebung.md`.

## Quick development setup

Backend:

```bash
cd backend
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -e ".[dev]"
cd ..
```

Frontend:

```bash
cd frontend
npm ci
cd ..
```

Run checks:

```bash
make format
make check
```

Start the development environment according to the Makefile/HOWTO:

```bash
make dev
```

## Database and migrations

Application data is stored in:

```text
data/db/health-coach.db
```

Schema changes are managed exclusively through Alembic:

```bash
make db-current
make db-history
make db-upgrade
make migration m="Beschreibung"
```

Do not use `create_all()` or manual SQLite schema edits as a replacement for migrations.

## Production

The production checkout lives under `/opt/health-coach`. Caddy serves `frontend/dist` and proxies `/api/*`, `/ws/*` and `/videos/*` to FastAPI. Runtime configuration lives under `/etc/health-coach/`.

The supported deployment/update entry point is:

```bash
cd /opt/health-coach
./deploy/provision.sh
```

An optional remote branch can be selected during provisioning; without one, the current branch is updated. The normal boot path uses `prepare.sh` and does not download dependencies or models.

See `DEPLOYMENT.md` for installation, Caddy/systemd, update workflow, kiosk operation, troubleshooting and recovery.

## Local LLM and TTS

The LLM is optional. It is used only for wording/explanation and never replaces deterministic workout or safety decisions. The default local model lives under `data/models/llm/`; Piper voices live under `data/models/piper-tts/`.

See `LOCAL-LLM.md` for the local model runtime and `DEPLOYMENT.md` for production service configuration.

## API and live channels

Typical endpoints/channels include:

```text
GET  /health
/api/...
/ws/device-agent
/ws/telemetry
/ws/coaching
/videos/...
```

Interactive FastAPI documentation is available directly from the backend at `/docs` when enabled/running.

## Testing, CI and dependency updates

GitHub Actions runs the project checks on pushes and pull requests. Typical local checks are:

```bash
make format-check
make check
```

Dependabot checks npm, pip and GitHub Actions dependencies according to `.github/dependabot.yml` (currently configured for daily checks).

## Documentation

| Document | Purpose |
|---|---|
| `README.md` | short project entry point |
| `arc42-digital-fitness-coach.md` | canonical architecture documentation (arc42 chapters 1–12 plus appendices) |
| `DEPLOYMENT.md` | Debian appliance deployment, systemd, Caddy, configuration, update and operations |
| `HOWTO-Entwicklungsumgebung.md` | local developer setup and troubleshooting |
| `LOCAL-LLM.md` | local LLM runtime/model usage |

The `_old.md` documentation variants are obsolete after consolidation and should not be maintained in parallel.
