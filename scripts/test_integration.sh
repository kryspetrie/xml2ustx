#!/usr/bin/env bash
# Automated integration smoke tests for xml2ustx + OpenUtau sidecar wiring.
#
# Runs:
#   1. CLI conversion (poetry / source)
#   2. PyInstaller sidecar conversion (OpenUtau-style args + XML2USTX_CONFIG)
#   3. Prints manual OpenUtau UI test steps
#
# Usage:
#   ./scripts/test_integration.sh
#   ./scripts/test_integration.sh --openutau-dir /path/to/OpenUtau-DiffSinger-Lunai
#   ./scripts/test_integration.sh --input tests/fixtures/minimal.musicxml --skip-sidecar-build
#   ./scripts/test_integration.sh --sidecar-dir /tmp/xml2ustx-sidecar
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
INPUT_FILE="$ROOT/tests/fixtures/minimal.musicxml"
CONFIG_FILE="$ROOT/src/resources/config.yml"
TRACK_CONFIG="default"
PROJECT_NAME="Integration Test"
OPENUTAU_DIR=""
SIDECAR_DIR=""
SKIP_SIDECAR_BUILD=0
WORK_DIR=""

platform_asset_suffix() {
  local os arch
  os="$(uname -s | tr '[:upper:]' '[:lower:]')"
  case "$(uname -m)" in
    x86_64 | amd64) arch="x64" ;;
    i386 | i686) arch="x86" ;;
    aarch64 | arm64) arch="arm64" ;;
    *) arch="$(uname -m)" ;;
  esac
  case "$os" in
    linux) echo "linux-$arch" ;;
    darwin) echo "osx-$arch" ;;
    mingw* | cygwin* | msys*) echo "win-$arch" ;;
    *) echo "$os-$arch" ;;
  esac
}

usage() {
  sed -n '2,12p' "$0" | sed 's/^# \?//'
  echo
  echo "Options:"
  echo "  --input PATH              MusicXML input (default: tests/fixtures/minimal.musicxml)"
  echo "  --config PATH             config.yml (default: src/resources/config.yml)"
  echo "  --track-config ID         track_config id (default: default)"
  echo "  --openutau-dir PATH       Lunai fork root (optional hints for step 3)"
  echo "  --sidecar-dir PATH        Use existing sidecar dir instead of building"
  echo "  --skip-sidecar-build      Skip PyInstaller sidecar test (CLI only)"
  echo "  -h, --help                Show this help"
}

while [ $# -gt 0 ]; do
  case "$1" in
    --input)
      INPUT_FILE="$2"
      shift 2
      ;;
    --config)
      CONFIG_FILE="$2"
      shift 2
      ;;
    --track-config)
      TRACK_CONFIG="$2"
      shift 2
      ;;
    --openutau-dir)
      OPENUTAU_DIR="$2"
      shift 2
      ;;
    --sidecar-dir)
      SIDECAR_DIR="$2"
      shift 2
      ;;
    --skip-sidecar-build)
      SKIP_SIDECAR_BUILD=1
      shift
      ;;
    -h | --help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

if [[ "$INPUT_FILE" != /* ]]; then
  INPUT_FILE="$ROOT/$INPUT_FILE"
fi
if [[ "$CONFIG_FILE" != /* ]]; then
  CONFIG_FILE="$ROOT/$CONFIG_FILE"
fi
if [ -n "$OPENUTAU_DIR" ] && [[ "$OPENUTAU_DIR" != /* ]]; then
  OPENUTAU_DIR="$(cd "$OPENUTAU_DIR" && pwd)"
fi
if [ -n "$SIDECAR_DIR" ] && [[ "$SIDECAR_DIR" != /* ]]; then
  SIDECAR_DIR="$(cd "$SIDECAR_DIR" && pwd)"
fi

WORK_DIR="$(mktemp -d "${TMPDIR:-/tmp}/xml2ustx-integration.XXXXXX")"
cleanup() {
  rm -rf "$WORK_DIR"
}
trap cleanup EXIT

pass() { echo "PASS: $*"; }
fail() { echo "FAIL: $*" >&2; exit 1; }
step() { echo; echo "== $* =="; }

require_file() {
  if [ ! -f "$1" ]; then
    fail "Missing file: $1"
  fi
}

require_file "$INPUT_FILE"
require_file "$CONFIG_FILE"

step "1/3  CLI conversion (source)"
cd "$ROOT"

if [ ! -d .venv ]; then
  echo "Creating .venv..."
  python3 -m venv .venv
fi
# shellcheck source=/dev/null
source .venv/bin/activate
python -m pip install -q --upgrade pip
pip install -q poetry
poetry install

CLI_OUT="$WORK_DIR/cli-test.ustx"
poetry run xml2ustx-cli \
  --input_file "$INPUT_FILE" \
  --output_file "$CLI_OUT" \
  --config_file "$CONFIG_FILE" \
  --project_name "$PROJECT_NAME" \
  --track_config "$TRACK_CONFIG"

require_file "$CLI_OUT"
grep -q "ustx_version" "$CLI_OUT" || fail "CLI output missing ustx_version marker"
pass "CLI wrote $CLI_OUT"

echo "Track configs in config file:"
poetry run xml2ustx-cli --list_track_configs --config_file "$CONFIG_FILE"

SIDECAR_BIN=""
SIDECAR_CONFIG=""

if [ "$SKIP_SIDECAR_BUILD" -eq 0 ]; then
  step "2/3  Sidecar conversion (OpenUtau-style)"

  if [ -n "$SIDECAR_DIR" ]; then
    echo "Using sidecar dir: $SIDECAR_DIR"
  elif [ -x "$ROOT/dist/sidecar/xml2ustx" ]; then
    SIDECAR_DIR="$ROOT/dist/sidecar"
    echo "Using existing sidecar: $SIDECAR_DIR/xml2ustx"
  elif [ -f "$ROOT/dist/sidecar/xml2ustx.exe" ]; then
    SIDECAR_DIR="$ROOT/dist/sidecar"
    echo "Using existing sidecar: $SIDECAR_DIR/xml2ustx.exe"
  else
    echo "Building PyInstaller sidecar (./scripts/build_sidecar.sh)..."
    "$ROOT/scripts/build_sidecar.sh" "$ROOT/dist/sidecar"
    SIDECAR_DIR="$ROOT/dist/sidecar"
  fi

  if [ -x "$SIDECAR_DIR/xml2ustx" ]; then
    SIDECAR_BIN="$SIDECAR_DIR/xml2ustx"
  elif [ -f "$SIDECAR_DIR/xml2ustx.exe" ]; then
    SIDECAR_BIN="$SIDECAR_DIR/xml2ustx.exe"
  else
    fail "Sidecar binary not found under $SIDECAR_DIR"
  fi

  if [ -f "$SIDECAR_DIR/default-config.yml" ]; then
    SIDECAR_CONFIG="$SIDECAR_DIR/default-config.yml"
  else
    SIDECAR_CONFIG="$CONFIG_FILE"
  fi

  OU_CONFIG="$WORK_DIR/openutau-config.yml"
  cp "$SIDECAR_CONFIG" "$OU_CONFIG"

  SIDECAR_OUT="$WORK_DIR/sidecar-test.ustx"
  export XML2USTX_CONFIG="$OU_CONFIG"

  echo "Invoking sidecar the same way OpenUtau does:"
  echo "  XML2USTX_CONFIG=$OU_CONFIG"
  echo "  $SIDECAR_BIN --input_file ... --output_file ... --config_file ... --track_config $TRACK_CONFIG"

  "$SIDECAR_BIN" \
    --input_file "$INPUT_FILE" \
    --output_file "$SIDECAR_OUT" \
    --config_file "$OU_CONFIG" \
    --project_name "$PROJECT_NAME" \
    --track_config "$TRACK_CONFIG"

  require_file "$SIDECAR_OUT"
  grep -q "ustx_version" "$SIDECAR_OUT" || fail "Sidecar output missing ustx_version marker"
  pass "Sidecar wrote $SIDECAR_OUT"
else
  step "2/3  Sidecar conversion (skipped)"
  echo "Skipped (--skip-sidecar-build)."
fi

step "3/3  Manual OpenUtau checks"

if [ -z "$OPENUTAU_DIR" ]; then
  for candidate in \
    "$ROOT/../OpenUtau-DiffSinger-Lunai" \
    "$HOME/dev/krys/OpenUtau-DiffSinger-Lunai"; do
    if [ -d "$candidate/OpenUtau" ]; then
      OPENUTAU_DIR="$(cd "$candidate" && pwd)"
      break
    fi
  done
fi

if [ -n "$OPENUTAU_DIR" ] && [ -d "$OPENUTAU_DIR/OpenUtau" ]; then
  PLATFORM_SUFFIX="$(platform_asset_suffix)"
  echo "Detected OpenUtau fork: $OPENUTAU_DIR"
  echo
  echo "Build bundled sidecar + OpenUtau:"
  echo "  cd $ROOT"
  echo "  OPENUTAU_TOOLS_DIR=\"$OPENUTAU_DIR/tools/xml2ustx\" \\"
  echo "    ./scripts/ci/build_and_package_sidecar.sh xml2ustx-$PLATFORM_SUFFIX \"$ROOT\""
  echo "  cd \"$OPENUTAU_DIR\""
  echo "  dotnet build OpenUtau"
  echo "  dotnet run --project OpenUtau"
else
  echo "OpenUtau fork not found. Clone and apply integration first:"
  echo "  git clone git@github.com:keirokeer/OpenUtau-DiffSinger-Lunai.git"
  echo "  $ROOT/integration/openutau/apply-integration.sh /path/to/OpenUtau-DiffSinger-Lunai"
fi

echo
echo "In the OpenUtau app, verify:"
echo "  • Tools → Edit MusicXML Import Config…  (YAML editor opens)"
echo "  • File → Import from MuseScore (MusicXML)…  (pick: $INPUT_FILE)"
echo "  • Track preset dropdown lists ids from config.yml"
echo "  • Import completes and notes appear on a track"
echo
echo "Typical paths (Linux):"
echo "  Bundled sidecar:  {OpenUtau install}/tools/xml2ustx/xml2ustx"
echo "  Downloaded:       ~/.local/share/OpenUtau/xml2ustx/sidecar/xml2ustx"
echo "  User config:      ~/.local/share/OpenUtau/xml2ustx/config.yml"
echo "  Logs:             ~/.local/share/OpenUtau/Logs/log.txt"
echo
echo "Download-path test (no bundled binary):"
echo "  rm -rf ~/.local/share/OpenUtau/xml2ustx/sidecar"
echo "  Tools → Download MusicXML Converter…"
echo "  Requires a published GitHub Release with xml2ustx-$(platform_asset_suffix).zip"
echo
echo "GitHub release assets check:"
echo "  curl -s https://api.github.com/repos/kryspetrie/xml2ustx/releases | jq '.[] | select(.draft==false) | {tag: .tag_name, assets: [.assets[].name]}'"

echo
pass "Automated integration checks finished."
