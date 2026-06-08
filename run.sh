#!/usr/bin/env bash
# Launch the xml2ustx CLI (Poetry console script).
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

if [ ! -d .venv ]; then
  python3 -m venv .venv
fi
# shellcheck source=/dev/null
source .venv/bin/activate

if ! command -v xml2ustx-cli >/dev/null 2>&1; then
  pip install -q poetry
  poetry install
fi

exec xml2ustx-cli "$@"
