#!/usr/bin/env bash
# CI/local: build installable native GUI app for the current OS/arch.
# Usage: build_gui_package.sh <artifact-base-name> [repo-root]
set -euo pipefail

ARTIFACT_NAME="${1:?artifact base name required}"
ROOT="${2:-$(cd "$(dirname "$0")/../.." && pwd)}"

cd "$ROOT"

python3 -m venv .venv
# shellcheck source=/dev/null
source .venv/bin/activate
python -m pip install --upgrade pip
pip install poetry pyinstaller
poetry install --no-interaction

# shellcheck source=/dev/null
source "$ROOT/scripts/ci/prepare_version.sh"

rm -rf build dist
run_pyinstaller() {
  pyinstaller --noconfirm xml2ustx-gui.spec
}

if [ "$(uname -s)" = "Darwin" ]; then
  host_arch="$(uname -m)"
  target_arch="${TARGET_ARCH:-$host_arch}"
  case "$target_arch" in
    arm64)
      if [ "$host_arch" = "arm64" ]; then
        run_pyinstaller
      else
        echo "Cannot build macOS arm64 binaries on $host_arch host" >&2
        exit 1
      fi
      ;;
    x64|x86_64)
      if [ "$host_arch" = "x86_64" ]; then
        run_pyinstaller
      elif [ "$host_arch" = "arm64" ]; then
        arch -x86_64 .venv/bin/pyinstaller --noconfirm xml2ustx-gui.spec
      else
        run_pyinstaller
      fi
      ;;
    *)
      run_pyinstaller
      ;;
  esac
else
  run_pyinstaller
fi

PKG_ROOT="$ROOT/gui-pkg"
rm -rf "$PKG_ROOT"
mkdir -p "$PKG_ROOT"

if [ "$(uname -s)" = "Darwin" ] && [ -d dist/xml2ustx.app ]; then
  cp -R dist/xml2ustx.app "$PKG_ROOT/"
  (cd "$PKG_ROOT" && zip -r "$ROOT/${ARTIFACT_NAME}.zip" xml2ustx.app)
  echo "Created $ROOT/${ARTIFACT_NAME}.zip (macOS .app)"
  exit 0
fi

if [ ! -d dist/xml2ustx ]; then
  echo "Expected dist/xml2ustx or dist/xml2ustx.app" >&2
  exit 1
fi

cp packaging/xml2ustx.desktop packaging/install-linux.sh "$PKG_ROOT/" 2>/dev/null || true
cp -a dist/xml2ustx "$PKG_ROOT/xml2ustx"
if [ -f packaging/xml2ustx.svg ]; then
  cp packaging/xml2ustx.svg "$PKG_ROOT/xml2ustx/"
fi
chmod +x "$PKG_ROOT/xml2ustx/xml2ustx" 2>/dev/null || true

cat > "$PKG_ROOT/install.sh" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
if [ "$(uname -s)" = "Darwin" ]; then
  echo "Drag xml2ustx.app to /Applications, or:"
  echo "  cp -R \"$DIR/xml2ustx.app\" /Applications/"
  exit 0
fi
if [ -f "$DIR/install-linux.sh" ]; then
  exec "$DIR/install-linux.sh" "$DIR/xml2ustx"
fi
echo "Run $DIR/xml2ustx/xml2ustx to start."
EOF
chmod +x "$PKG_ROOT/install.sh"

(cd "$PKG_ROOT" && zip -r "$ROOT/${ARTIFACT_NAME}.zip" .)
echo "Created $ROOT/${ARTIFACT_NAME}.zip"

if [ "$(uname -s)" = "Linux" ] && [ "$(uname -m)" = "x86_64" ]; then
  echo "Optional: ./scripts/ci/build_flatpak.sh ${ARTIFACT_NAME} \"$ROOT\""
fi
