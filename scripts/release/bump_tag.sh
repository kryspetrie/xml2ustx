#!/usr/bin/env bash
# Create the next semver git tag (vMAJOR.MINOR.PATCH) and optionally push it.
#
# Usage:
#   ./scripts/release/bump_tag.sh patch [--push]
#   ./scripts/release/bump_tag.sh minor --push
#   ./scripts/release/bump_tag.sh major --push
#
# Pushing a v* tag starts the Release workflow, which builds assets and
# publishes the GitHub Release automatically.
set -euo pipefail

BUMP="${1:-}"
PUSH=0
if [ "${2:-}" = "--push" ]; then
  PUSH=1
fi

if [ -z "$BUMP" ] || [[ ! "$BUMP" =~ ^(patch|minor|major)$ ]]; then
  echo "Usage: $0 <patch|minor|major> [--push]" >&2
  exit 1
fi

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

latest="$(git tag -l 'v[0-9]*' --sort=-v:refname | head -1 || true)"
if [ -z "$latest" ]; then
  latest="v0.0.0"
fi

ver="${latest#v}"
ver="${ver%%-*}"
IFS=. read -r major minor patch <<< "$ver"
major="${major:-0}"
minor="${minor:-0}"
patch="${patch:-0}"

case "$BUMP" in
  major)
    major=$((major + 1))
    minor=0
    patch=0
    ;;
  minor)
    minor=$((minor + 1))
    patch=0
    ;;
  patch)
    patch=$((patch + 1))
    ;;
esac

new_tag="v${major}.${minor}.${patch}"

if git rev-parse "$new_tag" >/dev/null 2>&1; then
  echo "Tag $new_tag already exists." >&2
  exit 1
fi

git tag -a "$new_tag" -m "Release $new_tag"
echo "Created tag $new_tag"

if [ "$PUSH" -eq 1 ]; then
  git push origin "$new_tag"
  echo "Pushed $new_tag — Release workflow will build assets and publish the GitHub Release."
else
  echo "Push to start the release build:"
  echo "  git push origin $new_tag"
fi
