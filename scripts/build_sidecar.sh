#!/usr/bin/env bash
# Build PyInstaller sidecar for the current OS/arch.
# Usage: ./scripts/build_sidecar.sh [output_dir]
# Example (OpenUtau publish folder): ./scripts/build_sidecar.sh ../OpenUtau/bin/linux-x64/tools/xml2ustx
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT_DIR="${1:-$ROOT/dist/sidecar}"

cd "$ROOT"

if [ ! -d .venv ]; then
  python3 -m venv .venv
fi
# shellcheck source=/dev/null
source .venv/bin/activate

pip install -q poetry pyinstaller
poetry install --no-root

rm -rf build dist
pyinstaller --noconfirm xml2ustx.spec

mkdir -p "$OUT_DIR"
if [ -f dist/xml2ustx.exe ]; then
  cp dist/xml2ustx.exe "$OUT_DIR/"
elif [ -f dist/xml2ustx ]; then
  cp dist/xml2ustx "$OUT_DIR/"
  chmod +x "$OUT_DIR/xml2ustx"
else
  echo "PyInstaller output not found under dist/" >&2
  exit 1
fi

echo "Sidecar installed to $OUT_DIR"
