.PHONY: dev backend device-agent frontend test check check-backend check-frontend format format-check build db-upgrade db-current db-history migration


# ---------------------------------------------------------------------------
# Platform configuration
# ---------------------------------------------------------------------------

ifeq ($(OS),Windows_NT)
PYTHON := .venv\Scripts\python.exe
SHELL := cmd.exe
else
PYTHON := .venv/bin/python
endif


# ---------------------------------------------------------------------------
# Development
# ---------------------------------------------------------------------------

ifeq ($(OS),Windows_NT)

dev:
	@powershell -NoProfile -Command \
		"$$ErrorActionPreference = 'Stop'; \
		Write-Host 'Starting Health Coach ...'; \
		Start-Process powershell -ArgumentList '-NoExit', '-NoProfile', '-Command', 'make backend'; \
		Start-Process powershell -ArgumentList '-NoExit', '-NoProfile', '-Command', 'make device-agent'; \
		Start-Process powershell -ArgumentList '-NoExit', '-NoProfile', '-Command', 'make frontend'"
else

dev:
	@set -eu; \
	backend_pid=""; \
	device_agent_pid=""; \
	frontend_pid=""; \
	cleanup() { \
		trap - INT TERM EXIT; \
		echo ""; \
		echo "Stopping Health Coach ..."; \
		if [ -n "$$device_agent_pid" ]; then \
			kill -TERM "$$device_agent_pid" 2>/dev/null || true; \
		fi; \
		if [ -n "$$backend_pid" ]; then \
			kill -TERM "$$backend_pid" 2>/dev/null || true; \
		fi; \
		if [ -n "$$frontend_pid" ]; then \
			kill -TERM "$$frontend_pid" 2>/dev/null || true; \
		fi; \
		wait 2>/dev/null || true; \
		echo "Health Coach stopped."; \
	}; \
	trap cleanup INT TERM EXIT; \
	$(MAKE) backend & backend_pid=$$!; \
	$(MAKE) device-agent & device_agent_pid=$$!; \
	$(MAKE) frontend & frontend_pid=$$!; \
	wait || true; \
	cleanup

endif


# ---------------------------------------------------------------------------
# Services
# ---------------------------------------------------------------------------

backend:
	cd backend && $(PYTHON) -m alembic upgrade head
	cd backend && $(PYTHON) -m uvicorn apps.api.main:app --host 0.0.0.0 --port 8000 --reload

device-agent:
	cd backend && $(PYTHON) -m apps.device_agent.main

frontend:
	cd frontend && npm run dev -- --host 0.0.0.0


# ---------------------------------------------------------------------------
# Tests / checks
# ---------------------------------------------------------------------------

test:
	cd backend && $(PYTHON) -m pytest
	cd frontend && npm test

check: format-check check-backend check-frontend

check-backend:
	cd backend && $(PYTHON) -m ruff check .
	cd backend && $(PYTHON) -m mypy apps features adapters
	cd backend && $(PYTHON) -m pytest

check-frontend:
	cd frontend && npm run lint
	cd frontend && npm run format:check
	cd frontend && npx tsc --noEmit
	cd frontend && npm run build
	cd frontend && npm test


# ---------------------------------------------------------------------------
# Formatting
# ---------------------------------------------------------------------------

format:
	cd backend && $(PYTHON) -m ruff format .
	cd backend && $(PYTHON) -m ruff check . --fix
	cd frontend && npm run format

format-check:
	cd backend && $(PYTHON) -m ruff format --check .
	cd frontend && npm run format:check


# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------

build: check
	cd frontend && npm run build


# ---------------------------------------------------------------------------
# Database / Alembic
# ---------------------------------------------------------------------------

db-upgrade:
	cd backend && $(PYTHON) -m alembic upgrade head

db-current:
	cd backend && $(PYTHON) -m alembic current

db-history:
	cd backend && $(PYTHON) -m alembic history

migration:
	cd backend && $(PYTHON) -m alembic revision --autogenerate -m "$(m)"
