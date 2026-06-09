# Distribution

This document covers install options, release artifacts, CI builds, verification, and platform-specific packaging notes.

## Install options

| Audience | Recommended install |
|----------|---------------------|
| End users (GUI) | Download `xml2ustx-gui-<platform>.zip` or the Linux AppImage from [GitHub Releases](https://github.com/kryspetrie/xml2ustx/releases) |
| CLI users | `pipx install .` or Poetry / `xml2ustx-cli` from source |
| Python users (dev or daily use) | `pipx install .` from a clone, or `pipx install git+https://github.com/kryspetrie/xml2ustx.git@vX.Y.Z` |
| Contributors | `poetry install`, then `source .venv/bin/activate` or `./run_native_ui.sh` |

See the [Installation](../README.md#installation) section in the README for full commands.

### pipx

pipx installs isolated apps with console scripts on `PATH` (usually `~/.local/bin`):

```bash
pipx install .
xml2ustx
xml2ustx-cli --help
```

No Poetry prefix, venv activation, or shell aliases required. Upgrade with `pipx upgrade xml2ustx`.

### Pre-built GUI (PyInstaller)

Release zips contain a self-contained `xml2ustx` executable (Python and dependencies bundled via PyInstaller).

**Linux (zip)**

```bash
unzip xml2ustx-gui-linux-x64.zip
./xml2ustx/xml2ustx
# optional menu install:
./install-linux.sh
```

**Linux (AppImage, x64 only)**

```bash
chmod +x xml2ustx-gui-linux-x64.AppImage
./xml2ustx-gui-linux-x64.AppImage
```

**Linux (Flatpak, x64 only)**

One-time setup (if Flatpak is not installed):

```bash
sudo apt install flatpak   # Debian/Ubuntu; use your distro’s package on Fedora, etc.
```

Install from a release bundle:

```bash
flatpak install --user ./xml2ustx-gui-linux-x64.flatpak
flatpak run org.xml2ustx.xml2ustx
```

The Flatpak uses the same PyInstaller GUI build as the zip and AppImage. **Open in OpenUtau** may need permission to launch host apps:

```bash
flatpak override --user org.xml2ustx.xml2ustx --talk-name=org.freedesktop.FlatPak --filesystem=home
```

Build locally after `./scripts/build_gui.sh` on Linux x64:

```bash
./scripts/ci/build_flatpak.sh xml2ustx-gui-linux-x64 "$(pwd)"
```

**macOS**

```bash
unzip xml2ustx-gui-osx-arm64.zip   # or osx-x64
cp -R xml2ustx.app /Applications/
open -a xml2ustx
```

Set **File → Set OpenUtau path…** to `/Applications/OpenUtau.app` if you use “Open in OpenUtau after conversion”.

**Windows**

```powershell
Expand-Archive xml2ustx-gui-win-x64.zip -DestinationPath .
.\xml2ustx\xml2ustx.exe
# or:
powershell -ExecutionPolicy Bypass -File install.ps1
```

## CI release builds (GitHub Actions)

Workflow: [`.github/workflows/release.yml`](../.github/workflows/release.yml)

**Trigger:** publishing a GitHub Release whose tag matches semver (`vX.Y.Z`). Draft releases do not upload assets until published.

**Jobs:**

| Job | Runner matrix | Output |
|-----|---------------|--------|
| `build-gui` | `windows-latest` (x64, x86), `windows-11-arm` (arm64), `ubuntu-latest` (x64), `ubuntu-24.04-arm` (arm64), `macos-15-intel` (x64 + arm64 cross-build) | `xml2ustx-gui-<platform>.zip` (+ AppImage and Flatpak for `linux-x64`) |
| `publish` | `ubuntu-latest` | Uploads GUI artifacts + `CHECKSUMS.sha256` to the release |

**Build scripts:**

- GUI: [`scripts/ci/build_gui_package.sh`](../scripts/ci/build_gui_package.sh) (Linux/macOS), [`scripts/ci/build_gui_package.ps1`](../scripts/ci/build_gui_package.ps1) (Windows)
- Flatpak (Linux x64, after GUI build): [`scripts/ci/build_flatpak.sh`](../scripts/ci/build_flatpak.sh) — manifest in [`packaging/flatpak/`](../packaging/flatpak/)
- Local equivalent: [`scripts/build_gui.sh`](../scripts/build_gui.sh)

PyInstaller spec: [`xml2ustx-gui.spec`](../xml2ustx-gui.spec) (GUI).

> **Sidecar builds are disabled in CI** until the OpenUtau fork that consumes them is published. Scripts remain under `scripts/build_sidecar.sh` and `scripts/ci/build_and_package_sidecar.*` for [`integration/openutau/`](../integration/openutau/) development.

Version embedded in builds comes from the release tag via `scripts/ci/prepare_version.sh` and `XML2USTX_VERSION`.

## Release artifacts

Published GitHub releases include:

| Artifact | Description |
|----------|-------------|
| `xml2ustx-gui-<platform>.zip` | Native Qt GUI (PyInstaller) + `install.sh` / `install.ps1` |
| `xml2ustx-gui-linux-x64.AppImage` | Linux GUI AppImage (x64 only) |
| `xml2ustx-gui-linux-x64.flatpak` | Linux GUI Flatpak bundle (x64 only) |
| `CHECKSUMS.sha256` | SHA256 digests for all uploaded files |

Platform suffixes: `win-x64`, `win-x86`, `win-arm64`, `linux-x64`, `linux-arm64`, `osx-x64`, `osx-arm64`.

## Verify downloads

After downloading a release asset:

```bash
sha256sum -c CHECKSUMS.sha256
```

On macOS:

```bash
shasum -a 256 -c CHECKSUMS.sha256
```

Only install or run binaries whose checksum matches the published value.

## Code signing and notarization

Release CI builds are **unsigned** by default. For public distribution:

### Windows

- Sign `xml2ustx.exe` / GUI executable with an Authenticode certificate (EV recommended for SmartScreen reputation).
- Use `signtool sign` after PyInstaller output is copied into the zip staging directory.

### macOS

- Sign the `.app` bundle with a Developer ID Application certificate.
- Notarize with `notarytool` and staple the ticket before zipping.
- Gatekeeper may block unsigned builds downloaded from the browser.

### Linux

- AppImage and zip bundles are typically distributed unsigned.
- Publish SHA256 checksums (included in releases) and optionally GPG-sign `CHECKSUMS.sha256`.

## Session logs

The CLI and GUI write timestamped session logs for each conversion job:

| Platform | Location |
|----------|----------|
| Linux | `~/.local/share/xml2ustx/logs/` |
| macOS | `~/Library/Logs/xml2ustx/` |
| Windows | `%LOCALAPPDATA%\xml2ustx\logs\` |

The log path is printed at the start of each job (`Session log: …`). The GUI also supports **Save log…** on the Convert tab.

## GUI settings on disk

Native UI preferences (theme, OpenUtau path, window layout, etc.) are stored via Qt `QSettings`:

| Platform | Typical location |
|----------|------------------|
| Linux | `~/.config/xml2ustx/native-ui.conf` |
| macOS | `~/Library/Preferences/com.xml2ustx.native-ui.plist` |
| Windows | Registry under `HKCU\Software\xml2ustx\native-ui` |
