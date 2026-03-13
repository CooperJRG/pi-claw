#!/usr/bin/env bash
set -euo pipefail

PI_HOST="${PI_HOST:-pi@raspberrypi.local}"
SERVICE_NAME="${SERVICE_NAME:-openclaw-display.service}"

ssh "${PI_HOST}" "sudo systemctl restart ${SERVICE_NAME} && sudo systemctl status ${SERVICE_NAME} --no-pager -l | head -n 20"
