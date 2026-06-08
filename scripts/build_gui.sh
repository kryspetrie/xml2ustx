#!/usr/bin/env bash
# Local: build installable GUI for this machine.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
NAME="xml2ustx-gui-$(uname -s | tr '[:upper:]' '[:lower:]')-$(uname -m)"
exec "$ROOT/scripts/ci/build_gui_package.sh" "$NAME" "$ROOT"
