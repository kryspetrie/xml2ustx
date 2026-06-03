#!/usr/bin/env bash
# CI: build PyInstaller sidecar and zip for the current runner OS/arch.
# Usage: build_and_package_sidecar.sh <artifact-base-name> [repo-root]
# Example: build_and_package_sidecar.sh xml2ustx-linux-x64
#
# Environment (optional):
#   TARGET_ARCH=arm64|x64  — macOS cross-build when runner is universal/intel
#   SKIP_POETRY_INSTALL=1
set -euo pipefail

ARTIFACT_NAME="${1:?artifact base name required (e.g. xml2ustx-linux-x64)}"
ROOT="${2:-$(cd "$(dirname "$0")/../.." && pwd)}"
WORK="$(cd "$ROOT/.." && pwd)"

cd "$ROOT"

python3 -m venv .venv
# shellcheck source=/dev/null
source .venv/bin/activate

python -m pip install --upgrade pip
pip install poetry pyinstaller

if [ "${SKIP_POETRY_INSTALL:-0}" != "1" ]; then
  poetry install --no-root
fi

rm -rf build dist

run_pyinstaller() {
  pyinstaller --noconfirm xml2ustx.spec
}

if [ "$(uname -s)" = "Darwin" ] && [ -n "${TARGET_ARCH:-}" ]; then
  case "$TARGET_ARCH" in
    arm64) arch -arm64 bash -c 'source .venv/bin/activate && pyinstaller --noconfirm xml2ustx.spec' ;;
    x64)   arch -x86_64 bash -c 'source .venv/bin/activate && pyinstaller --noconfirm xml2ustx.spec' ;;
    *)     run_pyinstaller ;;
  esac
else
  run_pyinstaller
fi

PKG_DIR="$WORK/sidecar-pkg"
rm -rf "$PKG_DIR"
mkdir -p "$PKG_DIR"

if [ -f dist/xml2ustx.exe ]; then
  cp dist/xml2ustx.exe "$PKG_DIR/"
elif [ -f dist/xml2ustx ]; then
  cp dist/xml2ustx "$PKG_DIR/"
  chmod +x "$PKG_DIR/xml2ustx"
else
  echo "PyInstaller output missing under $ROOT/dist" >&2
  exit 1
fi

cp src/resources/config.yml "$PKG_DIR/default-config.yml"

ZIP_PATH="$WORK/${ARTIFACT_NAME}.zip"
rm -f "$ZIP_PATH"
(cd "$PKG_DIR" && zip -r "$ZIP_PATH" .)

TOOLS_DIR="$WORK/OpenUtau/tools/xml2ustx"
mkdir -p "$TOOLS_DIR"
cp "$PKG_DIR/default-config.yml" "$TOOLS_DIR/"
if [ -f "$PKG_DIR/xml2ustx.exe" ]; then
  cp "$PKG_DIR/xml2ustx.exe" "$TOOLS_DIR/"
elif [ -f "$PKG_DIR/xml2ustx" ]; then
  cp "$PKG_DIR/xml2ustx" "$TOOLS_DIR/"
  chmod +x "$TOOLS_DIR/xml2ustx"
fi

echo "Created $ZIP_PATH"
echo "Installed sidecar to $TOOLS_DIR"
