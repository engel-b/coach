.PHONY: dev backend device-agent frontend test db-upgrade db-current db-history migration

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

backend:
	cd backend && \
	. .venv/bin/activate && \
  alembic upgrade head && \
	exec python -m uvicorn apps.api.main:app \
		--host 0.0.0.0 \
		--port 8000 \
		--reload

device-agent:
	cd backend && \
	. .venv/bin/activate && \
	exec python -m apps.device_agent.main

frontend:
	cd frontend && \
	exec npm run dev -- --host 0.0.0.0

test:
	cd backend && \
	. .venv/bin/activate && \
	python -m pytest

check: format-check check-backend check-frontend

check-backend:
	cd backend && \
	. .venv/bin/activate && \
	python -m ruff check . && \
	python -m mypy apps application domains adapters contracts && \
	python -m pytest

check-frontend:
	cd frontend && \
	npm run lint && \
	npx tsc --noEmit && \
  npm run build && \
  npm test

format:
	cd backend && \
	. .venv/bin/activate && \
	python -m ruff format . && \
	python -m ruff check . --fix

format-check:
	cd backend && \
	. .venv/bin/activate && \
	python -m ruff format --check .
  
build: check
	cd frontend && \
	npm run build

db-upgrade:
	cd backend && \
	. .venv/bin/activate && \
	alembic upgrade head

db-current:
	cd backend && \
	. .venv/bin/activate && \
	alembic current

db-history:
	cd backend && \
	. .venv/bin/activate && \
	alembic history

migration:
	cd backend && \
	. .venv/bin/activate && \
	alembic revision --autogenerate -m "$(m)"
