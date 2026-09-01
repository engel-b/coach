#!/usr/bin/env bash

set -euo pipefail

HEALTH_URL="http://127.0.0.1:8000/health"
APP_URL="http://127.0.0.1/"

echo "Waiting for Health Coach ..."

while ! curl --silent --fail --output /dev/null "${HEALTH_URL}"; do
    sleep 1
done

echo "Health Coach is ready. Starting Chromium."

exec chromium \
    --kiosk \
    --no-first-run \
    --disable-session-crashed-bubble \
    --disable-infobars \
    --autoplay-policy=no-user-gesture-required \
    "${APP_URL}"
