#!/usr/bin/env bash
# Install xml2ustx GUI from a PyInstaller dist/xml2ustx folder.
# Usage: ./packaging/install-linux.sh [path-to-dist/xml2ustx]
set -euo pipefail

SRC="${1:-$(cd "$(dirname "$0")/../dist/xml2ustx" && pwd)}"
INSTALL_ROOT="${XDG_DATA_HOME:-$HOME/.local/share}/xml2ustx"
DESKTOP_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/applications"
ICON_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/icons/hicolor/scalable/apps"

if [ ! -x "$SRC/xml2ustx" ]; then
  echo "Expected PyInstaller output at $SRC/xml2ustx" >&2
  exit 1
fi

mkdir -p "$INSTALL_ROOT" "$DESKTOP_DIR"
rm -rf "$INSTALL_ROOT"
cp -a "$SRC" "$INSTALL_ROOT/app"

DESKTOP_FILE="$DESKTOP_DIR/xml2ustx.desktop"
cat > "$DESKTOP_FILE" <<EOF
[Desktop Entry]
Type=Application
Name=xml2ustx
Comment=Convert MusicXML to OpenUtau USTX
Exec=$INSTALL_ROOT/app/xml2ustx %F
Icon=xml2ustx
Terminal=false
Categories=Audio;AudioVideo;
StartupWMClass=xml2ustx
EOF

if [ -f "$(dirname "$0")/xml2ustx.svg" ]; then
  mkdir -p "$ICON_DIR"
  cp "$(dirname "$0")/xml2ustx.svg" "$ICON_DIR/xml2ustx.svg"
fi

update-desktop-database "$DESKTOP_DIR" 2>/dev/null || true
echo "Installed to $INSTALL_ROOT/app"
echo "Desktop entry: $DESKTOP_FILE"
