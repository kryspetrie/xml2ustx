#!/usr/bin/env bash
# CI/local: bundle the PyInstaller GUI as a Flatpak (Linux x64).
# Usage: build_flatpak.sh <artifact-base-name> [repo-root]
# Requires gui-pkg/xml2ustx from build_gui_package.sh.
set -euo pipefail

ARTIFACT_NAME="${1:?artifact base name required}"
ROOT="${2:-$(cd "$(dirname "$0")/../.." && pwd)}"
FLATPAK_ID="org.xml2ustx.xml2ustx"
RUNTIME_VERSION="${FLATPAK_RUNTIME_VERSION:-24.08}"

cd "$ROOT"

if [ ! -x gui-pkg/xml2ustx/xml2ustx ]; then
  echo "Expected gui-pkg/xml2ustx from build_gui_package.sh" >&2
  exit 1
fi

# shellcheck source=/dev/null
source "$ROOT/scripts/ci/prepare_version.sh"

STAGING="$ROOT/packaging/flatpak/staging"
METAINFO="$ROOT/packaging/flatpak/org.xml2ustx.xml2ustx.metainfo.xml"
ICON="$ROOT/packaging/flatpak/icon.png"
BUILD_DIR="$ROOT/build-flatpak"
REPO_DIR="$ROOT/flatpak-repo"
OUTPUT="$ROOT/${ARTIFACT_NAME}.flatpak"
RELEASE_DATE="$(date -u +%Y-%m-%d)"

rm -rf "$STAGING" "$BUILD_DIR" "$REPO_DIR" "$OUTPUT" "$METAINFO" "$ICON"
mkdir -p "$STAGING/binary"
cp -a gui-pkg/xml2ustx/. "$STAGING/binary/"

sed \
  -e "s/@VERSION@/${XML2USTX_VERSION}/g" \
  -e "s/@DATE@/${RELEASE_DATE}/g" \
  "$ROOT/packaging/flatpak/org.xml2ustx.xml2ustx.metainfo.xml.in" \
  > "$METAINFO"

if [ ! -f "$METAINFO" ]; then
  echo "Failed to generate $METAINFO" >&2
  exit 1
fi

if ! command -v rsvg-convert >/dev/null 2>&1; then
  echo "rsvg-convert is required to build the Flatpak icon (e.g. apt install librsvg2-bin)" >&2
  exit 1
fi
rsvg-convert -w 512 -h 512 "$ROOT/packaging/xml2ustx.svg" -o "$ICON"

if [ ! -f "$ICON" ]; then
  echo "Failed to generate $ICON" >&2
  exit 1
fi

if ! command -v flatpak-builder >/dev/null 2>&1; then
  echo "flatpak-builder is required (e.g. apt install flatpak flatpak-builder)" >&2
  exit 1
fi

flatpak remote-add --user --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo
flatpak install -y --user flathub \
  "org.freedesktop.Platform//${RUNTIME_VERSION}" \
  "org.freedesktop.Sdk//${RUNTIME_VERSION}"

flatpak-builder \
  --force-clean \
  --user \
  --install-deps-from=flathub \
  --repo="$REPO_DIR" \
  "$BUILD_DIR" \
  "$ROOT/packaging/flatpak/org.xml2ustx.xml2ustx.yml"

flatpak build-bundle \
  --user \
  "$REPO_DIR" \
  "$OUTPUT" \
  "$FLATPAK_ID" \
  --runtime-repo=https://flathub.org/repo/flathub.flatpakrepo

echo "Created $OUTPUT"
