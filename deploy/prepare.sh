#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="${ROOT_DIR}/backend"
FRONTEND_DIR="${ROOT_DIR}/frontend"

echo "=== Health Coach: preparing installation ==="
echo "Repository: ${ROOT_DIR}"

#
# Python Virtual Environment
#
# Beim ersten Start wird die venv angelegt.
# Bei späteren Starts bleibt sie bestehen.
#
if [ ! -d "${BACKEND_DIR}/.venv" ]; then
    echo "Creating Python virtual environment ..."

    python3 -m venv "${BACKEND_DIR}/.venv"
fi

PYTHON="${BACKEND_DIR}/.venv/bin/python"
PIP="${BACKEND_DIR}/.venv/bin/pip"

#
# Backend-Abhängigkeiten
#
# Das darf auch bei unveränderten Abhängigkeiten laufen:
# pip erkennt bereits installierte Pakete.
#
echo "Installing backend dependencies ..."

"${PIP}" install --upgrade pip
"${PIP}" install -e "${BACKEND_DIR}"

#
# Frontend-Abhängigkeiten
#
# npm ci installiert exakt den Stand aus package-lock.json.
# Das ist für reproduzierbare Deployments besser als npm install.
#
echo "Installing frontend dependencies ..."

cd "${FRONTEND_DIR}"
npm ci

#
# Frontend bauen.
#
echo "Building frontend ..."

npm run build

#
# Datenbankschema auf den Stand des ausgecheckten Codes bringen.
#
echo "Applying database migrations ..."

cd "${BACKEND_DIR}"
"${PYTHON}" -m alembic upgrade head

echo "=== Health Coach: installation ready ==="

