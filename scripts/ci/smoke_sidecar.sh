#!/usr/bin/env bash
# Smoke-test a packaged sidecar zip against the minimal MusicXML fixture.
# Usage: smoke_sidecar.sh <artifact.zip>
set -euo pipefail

ZIP="${1:?artifact zip path required}"
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
WORKDIR="$(mktemp -d)"
trap 'rm -rf "$WORKDIR"' EXIT

unzip -q "$ZIP" -d "$WORKDIR"
SIDECAR="$WORKDIR/xml2ustx"
if [ ! -x "$SIDECAR" ]; then
  echo "Sidecar binary not found or not executable in $ZIP" >&2
  exit 1
fi

OUTPUT="$WORKDIR/minimal.ustx"
"$SIDECAR" \
  --input_file "$ROOT/tests/fixtures/minimal.musicxml" \
  --output_file "$OUTPUT" \
  --project_name "Smoke Test"

grep -q 'ustx_version' "$OUTPUT"
grep -q 'name: Smoke Test' "$OUTPUT"
echo "Sidecar smoke test passed: $OUTPUT"
