#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="${ROOT_DIR}/backend"
PYTHON="${BACKEND_DIR}/.venv/bin/python"

if [ ! -x "${PYTHON}" ]; then
    echo "Health Coach is not provisioned."
    exit 1
fi

cd "${BACKEND_DIR}"
"${PYTHON}" -m alembic upgrade head
