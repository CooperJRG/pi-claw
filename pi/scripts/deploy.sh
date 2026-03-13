#!/usr/bin/env bash
set -euo pipefail

PI_HOST="${PI_HOST:-pi@raspberrypi.local}"
TARGET_DIR="${TARGET_DIR:-/opt/openclaw-display}"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

rsync -az --delete \
  --exclude '.git/' \
  --exclude '__pycache__/' \
  --exclude '.pytest_cache/' \
  --exclude '.mypy_cache/' \
  --exclude '.venv/' \
  --exclude '.DS_Store' \
  "${REPO_ROOT}/" "${PI_HOST}:${TARGET_DIR}/"

echo "Deploy sync complete to ${PI_HOST}:${TARGET_DIR}"
