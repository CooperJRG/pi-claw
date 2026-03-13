#!/usr/bin/env bash
set -euo pipefail

PI_HOST="${PI_HOST:-pi@raspberrypi.local}"
SERVICE_NAME="${SERVICE_NAME:-openclaw-display.service}"
LINES="${LINES:-80}"
FOLLOW="${FOLLOW:-0}"

if [[ "${FOLLOW}" == "1" ]]; then
  ssh "${PI_HOST}" "sudo journalctl -u ${SERVICE_NAME} -f -n ${LINES}"
else
  ssh "${PI_HOST}" "sudo journalctl -u ${SERVICE_NAME} -n ${LINES} --no-pager"
fi
