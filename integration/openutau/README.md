# OpenUtau integration (bundled xml2ustx sidecar)

Target fork: **[keirokeer/OpenUtau-DiffSinger-Lunai](https://github.com/keirokeer/OpenUtau-DiffSinger-Lunai)**.

## Features

| Feature | Description |
|---------|-------------|
| **File → Import from MuseScore (MusicXML)...** | Converts via xml2ustx; prompts to download sidecar if missing |
| **Tools → Download MusicXML Converter...** | Manual download of platform zip from GitHub releases |
| **Tools → Edit MusicXML Import Config...** | YAML editor for voice/track presets |
| **CI** | Each OS matrix job builds Python via `scripts/ci/build_and_package_sidecar.*`; release includes `xml2ustx-{platform}.zip` and copies binary into `OpenUtau/tools/xml2ustx/` |
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

## Publish sidecar-only releases (xml2ustx repo)

```bash
# GitHub Actions → "Sidecar release" → tag e.g. sidecar-0.1.0
```

Or build locally: `./scripts/build_sidecar.sh ./dist` then zip with `default-config.yml`.

## Platform zip names

`xml2ustx-win-x64.zip`, `xml2ustx-win-x86.zip`, `xml2ustx-win-arm64.zip`, `xml2ustx-osx-x64.zip`, `xml2ustx-osx-arm64.zip`, `xml2ustx-linux-x64.zip`, `xml2ustx-linux-arm64.zip`

Each zip contains `xml2ustx` (or `.exe`) and `default-config.yml`.
