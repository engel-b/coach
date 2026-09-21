# Health Coach

Local digital fitness and health coach with live device telemetry,
workout recommendations, workout tracking, and training history.

> **Status:** Active development. The application currently supports
> person selection, check-ins, training recommendations, workout
> lifecycle/history, and live heart-rate telemetry. Bike telemetry
> infrastructure is prepared; concrete MERACH integration depends on the
> device/protocol.

[![CI](https://github.com/engel-b/coach/actions/workflows/ci.yml/badge.svg)](https://github.com/engel-b/coach/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![Node](https://img.shields.io/badge/node-24_LTS-green)
![License](https://img.shields.io/badge/license-private-lightgrey)

# Health Coach

## Overview

Health Coach is designed as a local application for a small number of
users. It combines health check-ins, rule-based training
recommendations, workout execution and live telemetry from fitness
devices.

The system is intentionally built as a modular monolith with clear
boundaries. The backend follows a Ports & Adapters / Hexagonal
Architecture approach so that domain logic remains independent of
FastAPI, SQLite, Bluetooth, and other infrastructure.

Typical application flow:

``` text
Select person
    ?
Dashboard / training history
    ?
Check-in
    ?
Training recommendation
    ?
Start workout
    ?
Live workout with heart rate / target values
    ?
Complete or abort workout
    ?
Workout summary
    ?
Dashboard / history
```

## Links

* Swagger UI, interactive API documentation with "Try it out": http://127.0.0.1:8000/docs 
* OpenAPI JSON, API contract: http://127.0.0.1:8000/openapi.json 
* ReDoc, alternative, human readable documentation: http://127.0.0.1:8000/redoc 

## Components

``` text
+-----------------------------+
� React / TypeScript Frontend �
� Vite                        �
+-----------------------------+
               � REST + WebSocket
               ?
+-----------------------------+
� FastAPI Backend             �
�                             �
� Application Services        �
� Domain Logic                �
� Persistence Adapters        �
+-----------------------------+
           �          �
           �          ?
           �     SQLite
           �     SQLAlchemy
           �     Alembic
           �
           � WebSocket
           ?
+-----------------------------+
� Device Agent                �
� Python / Bleak              �
+-----------------------------+
               � Bluetooth LE
               ?
        Fitness devices
        e.g. HR sensor
```

### Frontend

Technology:

-   React
-   TypeScript
-   Vite
-   REST API for application state
-   WebSocket for live telemetry

The frontend contains person selection, dashboard, check-in flow,
training recommendations, workout view, live heart-rate display, workout
summary, and training history.

### Backend API

Technology:

-   Python
-   FastAPI
-   Pydantic
-   SQLAlchemy
-   Alembic
-   SQLite
-   WebSockets

The backend contains the application and domain logic and exposes REST
and WebSocket endpoints.

Important architectural areas:

``` text
backend/
+-- apps/          # executable applications / entry points
+-- application/   # use cases and application services
+-- domains/       # business/domain logic
+-- adapters/      # persistence, Bluetooth, etc.
+-- contracts/     # API / message contracts
+-- tests/         # automated tests
```

### Device Agent

The Device Agent runs as a separate Python process. It discovers and
communicates with Bluetooth LE fitness devices and sends normalized
telemetry messages to the backend.

Current data flow for heart rate:

``` text
Heart-rate sensor
    ? Bluetooth LE
Bleak Device Agent
    ? WebSocket /ws/device-agent
FastAPI
    ? WebSocket /ws/telemetry
React frontend
```

The Device Agent has graceful shutdown handling so Bluetooth connections
can be closed cleanly when the application is stopped.

### Persistence

Application data is stored locally in SQLite:

``` text
data/db/health-coach.db
```

SQLAlchemy provides persistence access. Database schema changes are
managed exclusively through Alembic migrations.

The application creates the `data/` directory automatically if it does
not exist. On a fresh installation, Alembic still has to create/update
the database schema.

## Requirements

### Operating system

Development currently targets Linux. Bluetooth support relies on
BlueZ/Bluetooth LE.

### Python

Python 3.11 or newer is required according to `pyproject.toml`.

Check:

``` bash
python3 --version
```

### Node.js

Node.js 24 LTS is recommended for the frontend.

Check:

``` bash
node --version
npm --version
```

Using `nvm` is recommended for managing Node.js versions.

### Bluetooth

For BLE devices, a working Bluetooth adapter and BlueZ are required.

Useful checks:

``` bash
bluetoothctl show
systemctl status bluetooth
```

## Initial setup

Clone the repository and enter the project directory:

``` bash
git clone <repository-url>
cd Coach
```

### Backend

Create a virtual environment:

``` bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
```

Install the application including development dependencies:

``` bash
python -m pip install --upgrade pip
pip install -e ".[dev]"
```

Apply all database migrations:

``` bash
alembic upgrade head
```

Return to the repository root:

``` bash
cd ..
```

### Frontend

Install Node.js dependencies:

``` bash
cd frontend
npm ci
cd ..
```

## Starting the application

From the repository root:

``` bash
make dev
```

This starts the main development components:

``` text
FastAPI backend
Device Agent
React/Vite frontend
```

The backend also applies pending Alembic migrations before starting.

Stop the development environment with:

``` text
Ctrl+C
```

The launcher terminates the child processes and the Device Agent
performs a graceful shutdown of its Bluetooth connection.

### Starting components individually

Backend:

``` bash
cd backend
source .venv/bin/activate
alembic upgrade head
python -m uvicorn apps.api.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --reload
```

Device Agent:

``` bash
cd backend
source .venv/bin/activate
python -m apps.device_agent.main
```

Frontend:

``` bash
cd frontend
npm run dev -- --host 0.0.0.0
```

## Development commands

Run all automated checks:

``` bash
make check
```

This includes backend and frontend checks such as:

-   Ruff
-   mypy
-   pytest
-   ESLint
-   TypeScript compiler checks

Format backend code:

``` bash
make format
```

Check formatting without modifying files:

``` bash
make format-check
```

Build/check the project:

``` bash
make build
```

Run backend tests:

``` bash
make test
```

## Database and migrations

Show the current Alembic revision:

``` bash
make db-current
```

Show migration history:

``` bash
make db-history
```

Apply all pending migrations:

``` bash
make db-upgrade
```

Create a new migration using the project's migration target, if
configured:

``` bash
make migration
```

Do not manually modify the SQLite schema. Schema changes should be
represented by Alembic migrations so a fresh installation and CI can
reproduce the same database structure.

## API overview

Important API areas currently include:

``` text
/api/persons
/api/persons/{person_id}/...
/api/workouts/...
/api/devices

/ws/device-agent
/ws/telemetry
```

Examples of workout operations include starting a workout for a person,
completing or aborting a workout, retrieving workout history, and
retrieving a workout summary.

FastAPI's interactive API documentation is normally available while the
backend is running at:

``` text
http://localhost:8000/docs
```

## Live telemetry

Telemetry between processes uses generic messages rather than
device-specific frontend contracts.

Currently supported/planned telemetry types include:

``` text
device.status_changed
heart_rate.sample
bike.telemetry
```

This keeps the workout UI independent from a particular heart-rate
sensor or bike implementation.

## Testing and CI

GitHub Actions runs the project checks on pushes and pull requests.

A fresh CI runner has no existing SQLite database. Therefore the
workflow must initialize the database schema before API/persistence
tests run:

``` bash
cd backend
source .venv/bin/activate
alembic upgrade head
```

CI should use:

``` bash
make format-check
make check
```

rather than modifying source files with `make format`.

## Troubleshooting

### `sqlite3.OperationalError: unable to open database file`

SQLite can create a database file, but its parent directory must exist.

The application is expected to create:

``` text
data/
```

automatically.

Verify:

``` bash
ls -ld data
```

### `sqlite3.OperationalError: no such table: ...`

The SQLite file exists, but the database schema has not been migrated.

Run:

``` bash
cd backend
source .venv/bin/activate
alembic upgrade head
```

Then start or test the application again.

### Port 8000 is already in use

Check which process owns the port:

``` bash
ss -ltnp | grep :8000
```

If an old development process is still running, terminate that process
and restart:

``` bash
make dev
```

### Bluetooth error: `org.bluez.Error.InProgress`

A previous Bluetooth scan or process may still be active.

First check for duplicate Device Agent processes:

``` bash
ps aux | grep -E "device_agent|python.*Coach" | grep -v grep
```

Check the adapter:

``` bash
bluetoothctl show
```

If BlueZ is stuck, restart Bluetooth:

``` bash
sudo systemctl restart bluetooth
```

Then restart Health Coach.

### Heart-rate sensor does not appear

Check that:

1.  Bluetooth is enabled.
2.  The sensor is awake and being worn/activated.
3.  No second application is holding the BLE connection.
4.  Only one Device Agent instance is running.
5.  The backend and Device Agent WebSocket connection are active.

### Frontend has no live telemetry

Check that all three development components are running via:

``` bash
make dev
```

The expected chain is:

``` text
BLE device
? Device Agent
? /ws/device-agent
? backend
? /ws/telemetry
? frontend
```

Browser developer tools can be used to verify the `/ws/telemetry`
WebSocket connection.

### Development environment does not stop cleanly

Use `Ctrl+C` on the `make dev` process rather than killing individual
child processes where possible.

If a stale process remains:

``` bash
ps aux | grep -E "uvicorn|device_agent|vite" | grep -v grep
```

Terminate the stale process and, if Bluetooth remains busy, restart
BlueZ.

## Architecture principles

The project follows a few deliberate rules:

-   Domain logic should not depend on FastAPI, SQLite, Bluetooth, or
    React.
-   External systems are integrated through adapters.
-   Device-specific protocols should be normalized before reaching
    application/domain logic.
-   Database schema evolution is managed through Alembic.
-   Tests and CI should work from a clean environment.
-   Hardware integrations should be introduced without coupling workout
    logic to one specific device.

A Java/Spring comparison is roughly:

``` text
domains/       � domain model / pure business logic
application/   � application services / use cases
adapters/      � repository + infrastructure implementations
apps/api/      � REST/WebSocket application entry point
contracts/     � DTOs / wire contracts
SQLAlchemy     � JPA/Hibernate role
Alembic        � Flyway/Liquibase role
```

## Current capabilities

The application currently includes:

-   Multiple persons
-   Person dashboard
-   Health/readiness check-in
-   Training recommendation
-   Workout start, completion and abort
-   Workout phases and target heart-rate ranges
-   Workout summary
-   Training history
-   Live BLE heart-rate telemetry
-   Device connection status
-   Backend-to-frontend live WebSocket telemetry
-   SQLite persistence with Alembic migrations
-   Generic bike telemetry domain/application model
-   Automated backend/frontend quality checks

## Roadmap

Near-term development includes:

-   MERACH bike discovery and integration
-   Live bike telemetry such as power, cadence, speed and resistance
-   Bike-aware workout execution
-   Improved training recommendations using profile, check-in and
    workout history
-   Further test isolation, especially a dedicated test database

Possible later extensions include additional fitness-device adapters,
richer coaching, voice interaction, video/gamification, and other
health/fitness integrations.

## Repository status

This is currently a locally operated application under active
development. Hardware integrations can depend on the exact capabilities
and BLE/GATT protocol of the connected device.
