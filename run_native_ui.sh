#!/usr/bin/env bash
# Launch the native Qt6 desktop UI for xml2ustx.
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

if [ ! -d .venv ]; then
  python3 -m venv .venv
fi
# shellcheck source=/dev/null
source .venv/bin/activate

if ! python -c "import PySide6" 2>/dev/null; then
  pip install -q poetry
  poetry install
fi

exec xml2ustx "$@"
