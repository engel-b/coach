#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="${ROOT_DIR}/backend"
FRONTEND_DIR="${ROOT_DIR}/frontend"

PYTHON="${BACKEND_DIR}/.venv/bin/python"
PIP="${BACKEND_DIR}/.venv/bin/pip"

echo "=== Health Coach: update started ==="

cd "${ROOT_DIR}"

echo "Updating repository ..."
git pull --ff-only

echo "Current branch: $(git branch --show-current)"

echo "Ensuring Python virtual environment ..."
if [ ! -d "${BACKEND_DIR}/.venv" ]; then
    python3 -m venv "${BACKEND_DIR}/.venv"
fi

echo "Installing backend dependencies ..."
"${PIP}" install --upgrade pip
"${PIP}" install -e "${BACKEND_DIR}"

echo "Preparing runtime data directories ..."
mkdir -p \
    "${ROOT_DIR}/data/db" \
    "${ROOT_DIR}/data/models/llm" \
    "${ROOT_DIR}/data/models/piper-tts" \
    "${ROOT_DIR}/data/videos"

echo "Provisioning TTS voice ..."
"${PYTHON}" "${BACKEND_DIR}/scripts/ensure_tts_voice.py"

echo "Provisioning LLM model ..."
"${PYTHON}" "${BACKEND_DIR}/scripts/ensure_llm_model.py"

echo "Installing frontend dependencies ..."
cd "${FRONTEND_DIR}"
/usr/bin/npm ci

echo "Building frontend ..."
/usr/bin/npm run build

echo "Applying database migrations ..."
cd "${BACKEND_DIR}"
"${PYTHON}" -m alembic upgrade head

echo "Reloading systemd ..."
sudo /usr/bin/systemctl daemon-reload

echo "Restarting Health Coach services ..."
sudo systemctl restart health-coach-prepare.service
sudo systemctl restart health-coach-llm.service
sudo systemctl restart health-coach-api.service
sudo systemctl restart health-coach-device-agent.service

echo "=== Health Coach: update complete ==="
