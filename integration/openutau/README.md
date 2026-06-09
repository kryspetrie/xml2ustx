# OpenUtau integration (bundled xml2ustx sidecar)

Target fork: **[keirokeer/OpenUtau-DiffSinger-Lunai](https://github.com/keirokeer/OpenUtau-DiffSinger-Lunai)**.

## Features

| Feature | Description |
|---------|-------------|
| **File → Import from MuseScore (MusicXML)...** | Converts via xml2ustx; prompts to download sidecar if missing; prompts to remap missing singers to installed voices |
| **Tools → Download MusicXML Converter...** | Manual download of platform zip from GitHub releases |
| **Tools → Edit MusicXML Import Config...** | YAML editor for voice/track presets |
| **CI** | Sidecar packaging is **deferred** until an OpenUtau release ships this integration. Scripts remain under `scripts/ci/build_and_package_sidecar.*` for fork development. |
| **Bundled default config** | `tools/xml2ustx/default-config.yml` ships with the app (Lunai voices) |

## Download sources (automatic)

1. Latest **[keirokeer/OpenUtau-DiffSinger-Lunai](https://github.com/keirokeer/OpenUtau-DiffSinger-Lunai)** release asset `xml2ustx-{platform}.zip`
2. Fallback: latest **[kryspetrie/xml2ustx](https://github.com/kryspetrie/xml2ustx)** release with the same asset name

Installed to: `{DataPath}/xml2ustx/sidecar/`

## Apply to the Lunai fork

```bash
git clone git@github.com:keirokeer/OpenUtau-DiffSinger-Lunai.git
cd OpenUtau-DiffSinger-Lunai
/path/to/xml2ustx/integration/openutau/apply-integration.sh "$(pwd)"
dotnet build OpenUtau
```

Re-run `apply-integration.sh` after merging upstream OpenUtau if menus conflict.

## CI (xml2ustx repo)

The **Test** workflow (`.github/workflows/test.yml`) runs on push/PR to `main`:

- **ruff** lint (`src`, `tests`)
- **pytest** on Python 3.12 and 3.13 (Qt tests use `QT_QPA_PLATFORM=offscreen`)

The **Release** workflow builds **GUI packages only** (no sidecar zips) when a semver release is published, and uploads **`CHECKSUMS.sha256`**. See [docs/DISTRIBUTION.md](../../docs/DISTRIBUTION.md).

Sidecar smoke tests (`scripts/ci/smoke_sidecar.sh`) and release packaging can be run locally until the Lunai fork publishes a build that consumes them.

## Smoke test (xml2ustx repo)

```bash
./scripts/test_integration.sh
```

Runs CLI conversion against `tests/fixtures/minimal.musicxml`, builds/tests the PyInstaller sidecar with OpenUtau-style args, then prints manual OpenUtau UI steps. Options: `--skip-sidecar-build`, `--openutau-dir PATH`, `--sidecar-dir PATH`, `--input PATH`.

After building a release zip locally:

```bash
./scripts/ci/smoke_sidecar.sh xml2ustx-linux-x64.zip
```

## Publish releases (xml2ustx repo)

Releases use semver git tags (`v0.1.0`, `v1.2.3`, …). Published releases currently include native GUI packages and **`CHECKSUMS.sha256`** only — not sidecar zips (`xml2ustx-{platform}.zip`).

```bash
./scripts/release/bump_tag.sh patch --push   # push tag + publish release → starts CI
```

Or tag manually, then publish the release on GitHub (or with `gh release create v0.1.0`). **CI runs only when the release is published**, not on ordinary pushes or tag-only pushes.

## Platform zip names

`xml2ustx-win-x64.zip`, `xml2ustx-win-x86.zip`, `xml2ustx-win-arm64.zip`, `xml2ustx-osx-x64.zip`, `xml2ustx-osx-arm64.zip`, `xml2ustx-linux-x64.zip`, `xml2ustx-linux-arm64.zip`

Each zip contains `xml2ustx` (or `.exe`) and `default-config.yml`.
