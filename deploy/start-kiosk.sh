#!/usr/bin/env bash

set -euo pipefail

APP_URL="http://127.0.0.1"

exec chromium \
    --kiosk \
    --no-first-run \
    --disable-session-crashed-bubble \
    --disable-infobars \
    --autoplay-policy=no-user-gesture-required \
    "${APP_URL}/starting.html"