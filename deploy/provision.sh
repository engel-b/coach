#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="${ROOT_DIR}/backend"
FRONTEND_DIR="${ROOT_DIR}/frontend"
DATA_DIR="${ROOT_DIR}/data"

PYTHON="${BACKEND_DIR}/.venv/bin/python"
PIP="${BACKEND_DIR}/.venv/bin/pip"

BACKEND_ENV_TEMPLATE="${ROOT_DIR}/deploy/etc/health-coach/backend.env"
BACKEND_ENV_TARGET="/etc/health-coach/backend.env"
LLM_ENV_TEMPLATE="${ROOT_DIR}/deploy/etc/health-coach/llm.env"
LLM_ENV_TARGET="/etc/health-coach/llm.env"
CADDY_TEMPLATE="${ROOT_DIR}/deploy/etc/caddy/Caddyfile"
CADDY_TARGET="/etc/caddy/Caddyfile"
SYSTEMD_TEMPLATE_DIR="${ROOT_DIR}/deploy/etc/systemd/system"
SYSTEMD_TARGET_DIR="/etc/systemd/system"

ASSUME_YES=0
if [[ "${1:-}" == "--yes" ]]; then
    ASSUME_YES=1
elif [[ $# -gt 0 ]]; then
    echo "Usage: $0 [--yes]" >&2
    exit 2
fi

confirm() {
    local prompt="$1"
    local answer

    if [[ "${ASSUME_YES}" -eq 1 ]]; then
        echo "${prompt} [yes: --yes]"
        return 0
    fi

    if [[ ! -t 0 ]]; then
        echo "${prompt} [skipped: non-interactive]"
        return 1
    fi

    read -r -p "${prompt} [y/N] " answer
    [[ "${answer}" =~ ^[Yy]([Ee][Ss])?$ ]]
}

backup_file() {
    local target="$1"
    local timestamp
    timestamp="$(date +%Y%m%d-%H%M%S)"
    local backup="${target}.bak.${timestamp}"
    sudo cp -a "${target}" "${backup}"
    printf '%s' "${backup}"
}

read_root_file() {
    local target="$1"
    local destination="$2"
    sudo cat "${target}" > "${destination}"
}

env_keys() {
    local file="$1"
    awk -F= '/^[A-Za-z_][A-Za-z0-9_]*=/{print $1}' "${file}" | sort -u
}

sync_env_file() {
    local label="$1"
    local template="$2"
    local target="$3"

    echo "Checking ${label} ..."

    if [[ ! -f "${template}" ]]; then
        echo "ERROR: configuration template missing: ${template}" >&2
        exit 1
    fi

    if ! sudo test -f "${target}"; then
        echo "Configuration file is missing: ${target}"
        if confirm "Install ${label} from repository template?"; then
            sudo install -D -m 0644 "${template}" "${target}"
            echo "Installed ${target}"
        else
            echo "WARNING: ${target} remains missing."
        fi
        return
    fi

    local current_file
    local work_file
    local template_keys_file
    local current_keys_file
    local missing_keys_file
    local obsolete_keys_file
    current_file="$(mktemp)"
    work_file="$(mktemp)"
    template_keys_file="$(mktemp)"
    current_keys_file="$(mktemp)"
    missing_keys_file="$(mktemp)"
    obsolete_keys_file="$(mktemp)"
    read_root_file "${target}" "${current_file}"
    cp "${current_file}" "${work_file}"

    env_keys "${template}" > "${template_keys_file}"
    env_keys "${current_file}" > "${current_keys_file}"
    comm -23 "${template_keys_file}" "${current_keys_file}" > "${missing_keys_file}"
    comm -13 "${template_keys_file}" "${current_keys_file}" > "${obsolete_keys_file}"

    local changed=0

    if [[ -s "${missing_keys_file}" ]]; then
        echo "Missing variables in ${target}:"
        sed 's/^/  + /' "${missing_keys_file}"
        if confirm "Add the missing variables with template defaults?"; then
            printf '\n# Added by deploy/provision.sh\n' >> "${work_file}"
            while IFS= read -r key; do
                grep -m1 -E "^${key}=" "${template}" >> "${work_file}"
            done < "${missing_keys_file}"
            changed=1
        fi
    fi

    if [[ -s "${obsolete_keys_file}" ]]; then
        echo "Variables no longer present in the repository template:"
        sed 's/^/  - /' "${obsolete_keys_file}"
        if confirm "Remove these obsolete variables from ${target}?"; then
            while IFS= read -r key; do
                sed -i -E "/^${key}=/d" "${work_file}"
            done < "${obsolete_keys_file}"
            changed=1
        fi
    fi

    if [[ "${changed}" -eq 1 ]]; then
        local backup
        backup="$(backup_file "${target}")"
        sudo tee "${target}" < "${work_file}" > /dev/null
        echo "Updated ${target} (backup: ${backup})"
    elif [[ ! -s "${missing_keys_file}" && ! -s "${obsolete_keys_file}" ]]; then
        echo "${label} keys are complete. Existing values are preserved."
    else
        echo "${label} left unchanged. Existing values are preserved."
    fi

    rm -f \
        "${current_file}" \
        "${work_file}" \
        "${template_keys_file}" \
        "${current_keys_file}" \
        "${missing_keys_file}" \
        "${obsolete_keys_file}"
}

sync_managed_file() {
    local label="$1"
    local template="$2"
    local target="$3"

    if [[ ! -f "${template}" ]]; then
        echo "ERROR: managed template missing: ${template}" >&2
        exit 1
    fi

    if ! sudo test -f "${target}"; then
        echo "${label} is missing: ${target}"
        if confirm "Install ${label} from repository template?"; then
            sudo install -D -m 0644 "${template}" "${target}"
            echo "Installed ${target}"
            return 0
        fi
        echo "WARNING: ${label} remains missing."
        return 1
    fi

    if sudo cmp -s "${target}" "${template}"; then
        echo "${label} is up to date."
        return 1
    fi

    echo "${label} differs from the repository template:"
    sudo diff -u "${target}" "${template}" || true

    if confirm "Update ${label}?"; then
        local backup
        backup="$(backup_file "${target}")"
        sudo cp "${template}" "${target}"
        echo "Updated ${target} (backup: ${backup})"
        return 0
    fi

    echo "${label} left unchanged."
    return 1
}

migrate_file_if_needed() {
    local source="$1"
    local target="$2"

    if [[ -f "${source}" && ! -e "${target}" ]]; then
        mkdir -p "$(dirname "${target}")"
        echo "Moving legacy runtime file: ${source} -> ${target}"
        mv "${source}" "${target}"
    fi
}

load_runtime_environment() {
    set -a
    if [[ -r "${BACKEND_ENV_TARGET}" ]]; then
        # shellcheck disable=SC1090
        source "${BACKEND_ENV_TARGET}"
    fi
    if [[ -r "${LLM_ENV_TARGET}" ]]; then
        # shellcheck disable=SC1090
        source "${LLM_ENV_TARGET}"
    fi
    set +a
}

configure_runtime_data_layout() {
    echo "Preparing runtime data directories ..."
    mkdir -p \
        "${DATA_DIR}/db" \
        "${DATA_DIR}/models/llm" \
        "${DATA_DIR}/models/piper" \
        "${DATA_DIR}/videos"

    migrate_file_if_needed \
        "${BACKEND_DIR}/data/health-coach.db" \
        "${DATA_DIR}/db/health-coach.db"
    migrate_file_if_needed \
        "${BACKEND_DIR}/models/llm/qwen3.5-0.8b-q4_0.gguf" \
        "${DATA_DIR}/models/llm/qwen3.5-0.8b-q4_0.gguf"
    migrate_file_if_needed \
        "${BACKEND_DIR}/models/piper/de_DE-thorsten-medium.onnx" \
        "${DATA_DIR}/models/piper/de_DE-thorsten-medium.onnx"
    migrate_file_if_needed \
        "${BACKEND_DIR}/models/piper/de_DE-thorsten-medium.onnx.json" \
        "${DATA_DIR}/models/piper/de_DE-thorsten-medium.onnx.json"
}

sync_systemd_units() {
    local template
    local target

    echo "Checking systemd service files ..."
    for template in "${SYSTEMD_TEMPLATE_DIR}"/*.service; do
        [[ -e "${template}" ]] || continue
        target="${SYSTEMD_TARGET_DIR}/$(basename "${template}")"
        sync_managed_file \
            "systemd unit $(basename "${template}")" \
            "${template}" \
            "${target}" || true
    done

    echo "Reloading systemd unit definitions ..."
    sudo /usr/bin/systemctl daemon-reload
}

configure_caddy() {
    local previous_backup=""
    local updated=0

    echo "Checking Caddy configuration ..."

    if ! command -v caddy >/dev/null 2>&1; then
        echo "ERROR: caddy is not installed or not available in PATH." >&2
        exit 1
    fi

    if ! sudo test -f "${CADDY_TARGET}"; then
        echo "Caddyfile is missing: ${CADDY_TARGET}"
        if confirm "Install the Health Coach Caddyfile?"; then
            sudo install -D -m 0644 "${CADDY_TEMPLATE}" "${CADDY_TARGET}"
            updated=1
        else
            echo "ERROR: no Caddyfile available for validation." >&2
            exit 1
        fi
    elif ! sudo cmp -s "${CADDY_TARGET}" "${CADDY_TEMPLATE}"; then
        echo "Caddyfile differs from the repository template:"
        sudo diff -u "${CADDY_TARGET}" "${CADDY_TEMPLATE}" || true
        if confirm "Update ${CADDY_TARGET} from the repository template?"; then
            previous_backup="$(backup_file "${CADDY_TARGET}")"
            sudo cp "${CADDY_TEMPLATE}" "${CADDY_TARGET}"
            updated=1
            echo "Updated ${CADDY_TARGET} (backup: ${previous_backup})"
        else
            echo "Caddyfile left unchanged."
        fi
    else
        echo "Caddyfile is up to date."
    fi

    echo "Validating Caddy configuration ..."
    if ! sudo caddy validate --config "${CADDY_TARGET}" --adapter caddyfile; then
        if [[ "${updated}" -eq 1 ]]; then
            if [[ -n "${previous_backup}" ]]; then
                echo "Validation failed; restoring previous Caddyfile ..." >&2
                sudo cp "${previous_backup}" "${CADDY_TARGET}"
            else
                echo "Validation failed; removing newly installed Caddyfile ..." >&2
                sudo rm -f "${CADDY_TARGET}"
            fi
        fi
        echo "ERROR: Caddy configuration is invalid. Caddy was not restarted." >&2
        exit 1
    fi

    echo "Restarting Caddy ..."
    sudo /usr/bin/systemctl restart caddy.service
}

echo "=== Health Coach: update started ==="

cd "${ROOT_DIR}"

echo "Updating repository ..."
git pull --ff-only

echo "Current branch: $(git branch --show-current)"
echo "Current commit: $(git rev-parse --short HEAD)"

configure_runtime_data_layout

sync_env_file "backend environment" "${BACKEND_ENV_TEMPLATE}" "${BACKEND_ENV_TARGET}"
sync_env_file "LLM environment" "${LLM_ENV_TEMPLATE}" "${LLM_ENV_TARGET}"
load_runtime_environment

echo "Ensuring Python virtual environment ..."
if [[ ! -d "${BACKEND_DIR}/.venv" ]]; then
    python3 -m venv "${BACKEND_DIR}/.venv"
fi

echo "Installing backend dependencies ..."
"${PIP}" install --upgrade pip
"${PIP}" install -e "${BACKEND_DIR}"

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

sync_systemd_units

echo "Restarting Health Coach services ..."
sudo /usr/bin/systemctl restart health-coach-prepare.service
sudo /usr/bin/systemctl restart health-coach-llm.service
sudo /usr/bin/systemctl restart health-coach-api.service
sudo /usr/bin/systemctl restart health-coach-device-agent.service

configure_caddy

echo "=== Health Coach: update complete ==="
