#!/usr/bin/env bash
# Shared CI/local helper: resolve semver and bake it into src/application/_version.py.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"

if [ -z "${XML2USTX_VERSION:-}" ]; then
  if [ -n "${GITHUB_REF_NAME:-}" ]; then
    export XML2USTX_VERSION="${GITHUB_REF_NAME#v}"
  elif command -v poetry >/dev/null 2>&1; then
    export XML2USTX_VERSION="$(poetry version -s)"
  elif tag="$(git -C "$ROOT" describe --tags --match 'v[0-9]*' --abbrev=0 2>/dev/null)"; then
    export XML2USTX_VERSION="${tag#v}"
  else
    export XML2USTX_VERSION="0.0.0"
  fi
fi

python3 "$ROOT/scripts/ci/write_version_file.py" >/dev/null
echo "xml2ustx version: ${XML2USTX_VERSION}"
