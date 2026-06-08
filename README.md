# MusicXML to USTX

Convert MusicXML (`.mxl`, `.xml`, `.musicxml`, `.midi`) into [OpenUtau](https://github.com/stakira/OpenUtau) `.ustx` projects for singing voice synthesis.

This is a rewrite based on [nicolalandro/xml2ustx](https://github.com/nicolalandro/xml2ustx), with MuseScore-oriented parsing (via [music21](https://web.mit.edu/music21/)), track/voice presets, `.mxl` support, and rit/accel tempo handling.

## Contents

- [Requirements](#requirements)
- [Installation](#installation)
- [CLI application](#cli-application)
- [Sidecar](#sidecar)
- [Configuration](#configuration)
- [Native desktop app](#native-desktop-app)
- [OpenUtau integration](#openutau-integration)
- [Development and testing](#development-and-testing)
- [Releases and versioning](#releases-and-versioning)
- [Distribution](#distribution)
- [Limitations](#limitations)

---

## Requirements

Choose one install path below:

| Path | You need |
|------|----------|
| [Pre-built GUI / sidecar](#pre-built-executables-no-python) | Nothing (download from [GitHub Releases](https://github.com/kryspetrie/xml2ustx/releases)) |
| [pipx](#pipx-recommended-for-python-users) | Python 3.12+ and [pipx](https://pipx.pypa.io/) |
| [Poetry / virtualenv](#poetry-for-development) | Python 3.12+ and Poetry (or venv + Poetry) |

**System packages** (only when installing from source; used by music21 audio/export helpers on some code paths):

```bash
sudo apt install libmp3lame-dev ffmpeg   # Debian/Ubuntu
```

---

## Installation

### Pre-built executables (no Python)

Published [GitHub Releases](https://github.com/kryspetrie/xml2ustx/releases) include PyInstaller bundles that embed Python and dependencies. No `poetry run`, venv, or pip required.

| Artifact | Platforms | Use for |
|----------|-----------|---------|
| `xml2ustx-gui-<platform>.zip` | Windows, Linux, macOS (x64 + ARM64) | Native Qt desktop app |
| `xml2ustx-gui-linux-x64.AppImage` | Linux x64 | GUI without unpacking a zip |
| `xml2ustx-gui-linux-x64.flatpak` | Linux x64 | GUI installable via Flatpak |
| `xml2ustx-<platform>.zip` | Windows, Linux, macOS (x64 + ARM64) | CLI sidecar (OpenUtau / automation) |

`<platform>` is one of: `win-x64`, `win-x86`, `win-arm64`, `linux-x64`, `linux-arm64`, `osx-x64`, `osx-arm64`.

**Quick start (GUI):**

1. Download the zip (or AppImage on Linux x64) for your OS/arch from the latest `vX.Y.Z` release.
2. Verify with `CHECKSUMS.sha256` — see [docs/DISTRIBUTION.md](docs/DISTRIBUTION.md).
3. Run:
   - **Linux:** unzip, then `./xml2ustx/xml2ustx`; or run the AppImage / install the Flatpak (see [docs/DISTRIBUTION.md](docs/DISTRIBUTION.md))
   - **macOS:** unzip, then drag `xml2ustx.app` to Applications (or run from the zip)
   - **Windows:** unzip, then `xml2ustx\xml2ustx.exe` (or run `install.ps1` in the zip)

These builds are produced automatically by [`.github/workflows/release.yml`](.github/workflows/release.yml) when a semver release is **published** on GitHub.

### pipx (recommended for Python users)

[pipx](https://pipx.pypa.io/) installs `xml2ustx` and `xml2ustx-cli` into an isolated environment and puts commands on your `PATH` (typically `~/.local/bin`) — no `poetry run` and no shell aliases.

```bash
# From a clone (development checkout)
git clone https://github.com/kryspetrie/xml2ustx.git
cd xml2ustx
pipx install .

# Or install a release tag directly from GitHub
pipx install git+https://github.com/kryspetrie/xml2ustx.git@v0.1.0
```

Then run either command from any directory:

```bash
xml2ustx          # GUI
xml2ustx-cli --help
```

Upgrade or remove:

```bash
pipx upgrade xml2ustx
pipx uninstall xml2ustx
```

If `xml2ustx` is not found, ensure `~/.local/bin` is on your `PATH`. Most Linux login sessions include it by default; run `pipx ensurepath` once if needed.

### Poetry (for development)

```bash
git clone https://github.com/kryspetrie/xml2ustx.git
cd xml2ustx
poetry install
```

Run commands without `poetry run` by activating the project venv:

```bash
source .venv/bin/activate   # Windows: .venv\Scripts\activate
xml2ustx
xml2ustx-cli --help
```

Or use the repo wrappers (no activation, no `poetry run`):

```bash
./run_native_ui.sh    # GUI
./run.sh              # CLI
```

With Poetry but without activating the venv:

```bash
poetry run xml2ustx-cli --help
```

### Virtualenv

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install poetry
poetry install
xml2ustx-cli --help
```

### Verify install

```bash
QT_QPA_PLATFORM=offscreen poetry run pytest -q
./scripts/test_integration.sh --skip-sidecar-build
```

The integration script defaults to `tests/fixtures/minimal.musicxml`. Omit `--skip-sidecar-build` to also exercise a PyInstaller sidecar build.

---

## CLI application

The CLI is the core converter. It reads a MusicXML file (or a directory of files), applies voice/track settings from `config.yml`, and writes one `.ustx` file per input.

### Quick start

```bash
xml2ustx-cli \
  --input_file tests/fixtures/minimal.musicxml \
  --output_file output.ustx \
  --track_config default
```

Open `output.ustx` in OpenUtau.

### Command-line options

| Option | Description |
|--------|-------------|
| `--input_file PATH` | Single input: `.xml`, `.musicxml`, `.mxl`, `.mid`, `.midi` |
| `--input_dir PATH` | Convert every matching file in a directory (batch mode) |
| `--output_file PATH` | Output `.ustx` path (for `--input_file`; `.ustx` appended if missing) |
| `--project_name NAME` | Project title stored in the USTX metadata (default: `My Project`) |
| `--config_file PATH` | Path to `config.yml` (see [Config resolution](#config-resolution)) |
| `--track_config ID` | Track preset id from `config.yml` (e.g. `ttbb-barbershop`) |
| `--voice ID` | Per-track voice id (repeat for multiple tracks; ignored when `--track_config` is set) |
| `--pan VALUE` | Per-track pan, −100.0 to 100.0 (repeatable) |
| `--volume VALUE` | Per-track volume, −10.0 to 10.0 (repeatable) |
| `--track NAME` | Per-track display name (repeatable) |
| `--list_track_configs` | Print available `track_config` ids and exit |
| `--open` | Open output file(s) in OpenUtau after a successful conversion |
| `--openutau PATH` | Path to the OpenUtau executable (see [Open in OpenUtau](#open-in-openutau)) |
| `--debug` | Print parsed arguments and extra diagnostics |
| `--version` | Print version and exit |
| `-h`, `--help` | Show help |

**Rules:**

- Provide exactly one of `--input_file` or `--input_dir`.
- `--track_config` **overrides** `--voice`, `--pan`, `--volume`, and `--track`.
- Without `--track_config`, repeat `--voice` / `--pan` / `--volume` / `--track` to define tracks in order.
- Batch mode (`--input_dir`) writes `<stem>.ustx` next to each input file; `--output_file` is not used.

### Config resolution

The config file is chosen in this order:

1. `--config_file` on the command line
2. Environment variable **`XML2USTX_CONFIG`**
3. Bundled default: `src/resources/config.yml` (or the copy inside a PyInstaller bundle)

List presets in a config file:

```bash
xml2ustx-cli --list_track_configs
xml2ustx-cli --list_track_configs --config_file /path/to/config.yml
```

### Examples

**Single file with a track preset**

```bash
xml2ustx-cli \
  --input_file score.mxl \
  --output_file my-song.ustx \
  --project_name "My Song" \
  --track_config ttbb-barbershop
```

**Single file, manual per-track settings**

```bash
xml2ustx-cli \
  --input_file score.musicxml \
  --output_file duo.ustx \
  --voice tiger \
  --track "Lead" \
  --voice nero \
  --track "Bass" \
  --pan -25 \
  --pan 10
```

**Batch convert a folder**

```bash
xml2ustx-cli \
  --input_dir ./scores \
  --track_config default
```

**Custom config via environment**

```bash
export XML2USTX_CONFIG="$HOME/.config/xml2ustx/config.yml"
xml2ustx-cli --input_file score.xml --output_file out.ustx
```

### Exit codes

| Code | Meaning |
|------|---------|
| `0` | Success |
| `1` | Error (invalid args, missing input, conversion failure, bad config) |

Errors are printed to stderr (structured errors include a code prefix such as `[cancelled]`).

### Session logs

Each conversion job writes a timestamped log file. The path is printed at startup:

```text
Session log: ~/.local/share/xml2ustx/logs/20260603-120000-My Project.log
```

| Platform | Location |
|----------|----------|
| Linux | `~/.local/share/xml2ustx/logs/` |
| macOS | `~/Library/Logs/xml2ustx/` |
| Windows | `%LOCALAPPDATA%\xml2ustx\logs\` |

In the native GUI, use **Copy log** or **Save log…** on the Convert tab. See [docs/DISTRIBUTION.md](docs/DISTRIBUTION.md) for release verification and packaging notes.

### Open in OpenUtau

OpenUtau is **not** a command-line tool — there is no `openutau`/`OpenUtau` alias on PATH after a normal install, and it has no documented CLI flags. However, the **standalone app binary** has an undocumented startup behavior: if you launch it with **exactly one** extra argument that is an existing file path, it opens that project on startup (see `MainWindowViewModel` in the OpenUtau source).

That only works when you invoke the **real executable**, with a **full path**:

```bash
# Linux (extracted release zip)
~/OpenUtau-linux-x64/OpenUtau /absolute/path/to/output.ustx

# Linux AppImage
~/Applications/OpenUtau-x86_64.AppImage /absolute/path/to/output.ustx

# macOS
/Applications/OpenUtau.app/Contents/MacOS/OpenUtau /absolute/path/to/output.ustx

# Windows (from install/portable folder)
"C:\Program Files\OpenUtau\OpenUtau.exe" C:\path\to\output.ustx
```

**Caveats:**

- **`OpenUtau out.ustx` will not work** unless you have manually symlinked the binary onto your `PATH`.
- **`dotnet run --project OpenUtau -- out.ustx` usually does not work** — the startup check requires `GetCommandLineArgs().Length == 2`, which typically fails under `dotnet run` (extra host arguments).
- **Single-instance behavior** — if OpenUtau is already running, launching it again exits immediately and **does not** open the new file.
- **`xdg-open` / `open out.ustx`** only works if you have registered a `.ustx` file association (the bundled `.desktop` file does not define one).

#### `--open` flag (xml2ustx CLI)

Pass **`--open`** to launch OpenUtau after conversion. You almost always need to point at the binary explicitly:

```bash
export OPENUTAU_PATH="$HOME/OpenUtau-linux-x64/OpenUtau"
xml2ustx-cli \
  --input_file tests/fixtures/minimal.musicxml \
  --output_file output.ustx \
  --track_config default \
  --open

# or per invocation
xml2ustx-cli ... --open --openutau "$HOME/OpenUtau-linux-x64/OpenUtau"
```

**Resolution order:** `--openutau` → `OPENUTAU_PATH` → `OpenUtau` on `PATH` (rare) → a few common install paths.

If the binary is not found, conversion still succeeds; use **File → Open** in OpenUtau manually.

#### Alternatives that always work

- **OpenUtau menu:** File → Open → pick the `.ustx`
- **OpenUtau + integration:** File → Import from MuseScore (MusicXML)… (converts inside the app)
- **Native GUI:** `xml2ustx` then use “Open output folder” or **Save log…**

Batch mode (`--input_dir --open`) tries to spawn one OpenUtau process per output file (subject to the single-instance limitation above).

---

## Sidecar

A **sidecar** is a standalone PyInstaller binary (`xml2ustx` or `xml2ustx.exe`) that embeds Python and dependencies. Host applications (especially OpenUtau) invoke it as a subprocess instead of requiring a system Python install.

### What ships in a sidecar zip

Release assets are named `xml2ustx-{platform}.zip`:

| Platform | Zip name |
|----------|----------|
| Windows x64 | `xml2ustx-win-x64.zip` |
| Windows x86 | `xml2ustx-win-x86.zip` |
| Windows ARM64 | `xml2ustx-win-arm64.zip` |
| macOS x64 | `xml2ustx-osx-x64.zip` |
| macOS ARM64 | `xml2ustx-osx-arm64.zip` |
| Linux x64 | `xml2ustx-linux-x64.zip` |
| Linux ARM64 | `xml2ustx-linux-arm64.zip` |

Each zip contains:

```
xml2ustx          # or xml2ustx.exe on Windows
default-config.yml
```

Download from [GitHub Releases](https://github.com/kryspetrie/xml2ustx/releases) after a published semver release (`vX.Y.Z`).

### Building the sidecar locally

Build on the **target OS** (or use CI release artifacts):

```bash
# Binary only → dist/sidecar/
./scripts/build_sidecar.sh

# Packaged zip (same layout as GitHub releases)
./scripts/ci/build_and_package_sidecar.sh xml2ustx-linux-x64 "$(pwd)"
# → xml2ustx-linux-x64.zip in repo root
```

### Loading / installing the sidecar

#### Option A — OpenUtau (automatic)

For [OpenUtau-DiffSinger-Lunai](https://github.com/keirokeer/OpenUtau-DiffSinger-Lunai) with the integration applied ([guide](integration/openutau/README.md)):

1. **Bundled at build time** — copy the sidecar into the app tree before building OpenUtau:

   ```bash
   OPENUTAU_TOOLS_DIR=/path/to/OpenUtau-DiffSinger-Lunai/tools/xml2ustx \
     ./scripts/ci/build_and_package_sidecar.sh xml2ustx-linux-x64 "$(pwd)"
   cd /path/to/OpenUtau-DiffSinger-Lunai
   dotnet build OpenUtau
   ```

   Installed path: `{OpenUtau app}/tools/xml2ustx/xml2ustx`

2. **Download at runtime** — in OpenUtau: **Tools → Download MusicXML Converter…**  
   Fetches the latest release zip from GitHub and extracts to:

   | OS | Path |
   |----|------|
   | Linux | `~/.local/share/OpenUtau/xml2ustx/sidecar/` |
   | macOS | `~/Library/OpenUtau/xml2ustx/sidecar/` |
   | Windows | `%LOCALAPPDATA%\OpenUtau\xml2ustx\sidecar\` |

   Downloaded sidecar takes precedence over the bundled copy.

#### Option B — Manual install (any host)

```bash
unzip xml2ustx-linux-x64.zip -d ~/.local/share/xml2ustx
chmod +x ~/.local/share/xml2ustx/xml2ustx
```

Point your host at `~/.local/share/xml2ustx/xml2ustx` and a config file (see below).

#### Option C — Run from build output (development)

```bash
./scripts/build_sidecar.sh
./dist/sidecar/xml2ustx --help
```

### Using the sidecar

The sidecar exposes the **same CLI** as `xml2ustx-cli`. Hosts should invoke it as a subprocess with no shell, capture stderr on failure, and pass absolute paths.

**Minimal invocation**

```bash
./xml2ustx \
  --input_file /path/to/score.musicxml \
  --output_file /path/to/output.ustx \
  --config_file /path/to/config.yml \
  --project_name "My Project" \
  --track_config default
```

**Environment variables**

| Variable | Purpose |
|----------|---------|
| `XML2USTX_CONFIG` | Default config path when `--config_file` is omitted (OpenUtau sets this) |

**OpenUtau invocation (reference)**

OpenUtau runs the sidecar equivalent to:

```bash
cd "{sidecar_directory}"
XML2USTX_CONFIG="{user_config.yml}" \
  ./xml2ustx \
  --input_file "{input.musicxml}" \
  --output_file "{temp}.ustx" \
  --config_file "{user_config.yml}" \
  --project_name "{project name}" \
  --track_config "{preset id}"
```

- **Sidecar directory**: `tools/xml2ustx/` (bundled) or `{DataPath}/xml2ustx/sidecar/` (downloaded)
- **User config**: `{DataPath}/xml2ustx/config.yml` (created from `default-config.yml` on first use)
- **Working directory**: sidecar directory (so bundled resources resolve correctly)
- On success, OpenUtau loads the temp `.ustx` and deletes it

**Manual sidecar test (matches OpenUtau)**

```bash
SIDECAR=./dist/sidecar
CONFIG=/tmp/xml2ustx-config.yml
cp "$SIDECAR/default-config.yml" "$CONFIG"

export XML2USTX_CONFIG="$CONFIG"
"$SIDECAR/xml2ustx" \
  --input_file tests/fixtures/minimal.musicxml \
  --output_file /tmp/test.ustx \
  --config_file "$CONFIG" \
  --project_name "Sidecar test" \
  --track_config default
```

**Automated smoke test**

```bash
./scripts/test_integration.sh
./scripts/test_integration.sh --openutau-dir /path/to/OpenUtau-DiffSinger-Lunai
./scripts/test_integration.sh --skip-sidecar-build   # CLI only
```

### Integrating another host application

To call xml2ustx from your own app:

1. Ship or download the platform zip for your OS/arch.
2. Store user config separately (copy `default-config.yml` → `config.yml` on first run).
3. Spawn `{sidecar}/xml2ustx` with the arguments above; set `XML2USTX_CONFIG`.
4. Parse `--list_track_configs` output to populate preset dropdowns.
5. Load the resulting `.ustx` in OpenUtau, or parse it yourself (OpenUtau project format).

See `integration/openutau/OpenUtau.Core/Format/Xml2ustx.cs` for a complete C# reference implementation.

---

## Configuration

Voice and track presets live in **`config.yml`**. The shipped default is `src/resources/config.yml`.

### Voice presets (`voice_config`)

Each voice is referenced by `id`. There must always be a `default` entry. Add entries after installing singers in OpenUtau — inspect a saved `.ustx` in a text editor to find `phonemizer`, `renderer`, and `singer` values.

```yaml
voice_config:
  - id: 'default'
    phonemizer: 'OpenUtau.Core.DefaultPhonemizer'
  - id: 'tiger'
    singer: 'TIGER_DS_v106'
    renderer: 'DIFFSINGER'
    phonemizer: 'OpenUtau.Core.DiffSinger.DiffSingerARPAPlusEnglishPhonemizer'
  - id: 'nero'
    singer: 'Nero_v110/configs'
    renderer: 'DIFFSINGER'
    phonemizer: 'OpenUtau.Core.DiffSinger.DiffSingerARPAPlusEnglishPhonemizer'
```

### Track presets (`track_config`)

Presets assign voices, names, pan, and volume to new tracks. There must always be a `default` preset. Reference presets with `--track_config` or from the OpenUtau import dialog.

```yaml
track_config:
  - id: 'default'
    tracks:
      - voice_id: 'default'
  - id: 'ttbb-barbershop'
    tracks:
      - track_name: 'Tenor'
        voice_id: 'tiger'
        pan: -60
        volume: 0
      - track_name: 'Lead'
        voice_id: 'tiger'
        pan: -25
        volume: 3
      - track_name: 'Bari'
        voice_id: 'tiger'
        pan: -60
        volume: 0
      - track_name: 'Bass'
        voice_id: 'nero'
        pan: 10
        volume: 6
```

Edit config via the native GUI (**Config** tab) or OpenUtau (**Tools → Edit MusicXML Import Config…**).

---

## Native desktop app

Cross-platform **Qt6** UI (PySide6): drag-and-drop, full CLI options, visual + YAML config editor, theme (light/dark/system), OpenUtau launch, background conversion with cancel/progress, and session log export.

**Run the GUI:**

| Method | Command |
|--------|---------|
| Pre-built release | Download `xml2ustx-gui-<platform>.zip` — see [Pre-built executables](#pre-built-executables-no-python) |
| pipx | `pipx install .` then `xml2ustx` |
| Project venv | `source .venv/bin/activate` then `xml2ustx` |
| Wrapper script | `./run_native_ui.sh` |

Keyboard shortcuts: **Ctrl+O** open input, **Ctrl+Return** convert, **Ctrl+S** save config, **Ctrl+,** configuration tab. **View → Theme** switches light/dark/system appearance.

The GUI blocks tab switches and window close while a conversion is running. Unsaved config changes are saved before convert when you confirm the prompt.

Run the Python test suite (includes Qt UI tests):

```bash
QT_QPA_PLATFORM=offscreen poetry run pytest
```

Build a standalone executable locally (PyInstaller, same approach as CI):

```bash
./scripts/build_gui.sh
# → xml2ustx-gui-<os>-<arch>.zip in the repo root
```

CI builds for all major platforms are described in [docs/DISTRIBUTION.md](docs/DISTRIBUTION.md) and ship on [GitHub Releases](https://github.com/kryspetrie/xml2ustx/releases) when a semver tag is published.

---

## OpenUtau integration

Bundled sidecar + menu items for [OpenUtau-DiffSinger-Lunai](https://github.com/keirokeer/OpenUtau-DiffSinger-Lunai):

- **File → Import from MuseScore (MusicXML)...**
- **Tools → Download MusicXML Converter...**
- **Tools → Edit MusicXML Import Config...**

Apply the patch kit and full details: **[integration/openutau/README.md](integration/openutau/README.md)**

---

## Development and testing

### Console entry points

Installed by `poetry install`:

| Command | Role |
|---------|------|
| `xml2ustx-cli` | CLI converter |
| `xml2ustx` / `xml2ustx-gui` | Native Qt GUI |

Legacy module entry points (`main.py`, `native_ui.py`) remain for compatibility but are not recommended.

### Unit tests

Component-level tests build domain models directly; one small MusicXML fixture (`tests/fixtures/minimal.musicxml`) covers the parse → export wiring.

```bash
QT_QPA_PLATFORM=offscreen poetry run pytest -q
poetry run ruff check src tests
```

CI (`.github/workflows/test.yml`) runs ruff, pytest on Python 3.12 and 3.13, and a Linux sidecar smoke build.

### Integration smoke test

```bash
./scripts/test_integration.sh --skip-sidecar-build   # CLI only (fast)
./scripts/test_integration.sh                        # CLI + PyInstaller sidecar
./scripts/ci/smoke_sidecar.sh xml2ustx-linux-x64.zip   # after building a release zip
```

---

## Releases and versioning

Versioning follows **[Semantic Versioning](https://semver.org/)** (`vMAJOR.MINOR.PATCH` git tags) via [poetry-dynamic-versioning](https://github.com/mtkennerly/poetry-dynamic-versioning).

**Create a release** (builds run only when the GitHub Release is **published**):

```bash
./scripts/release/bump_tag.sh patch --push   # requires gh CLI
```

Or manually:

```bash
git tag -a v0.1.0 -m "Release v0.1.0"
git push origin v0.1.0
gh release create v0.1.0 --title "xml2ustx v0.1.0" --generate-notes
```

The **Release** workflow (GitHub Actions on `windows-latest`, `ubuntu-latest`, `ubuntu-24.04-arm`, `macos-15-intel`, and `windows-11-arm`) uploads PyInstaller **GUI** zips, **CLI sidecar** zips, a Linux x64 **AppImage**, a Linux x64 **Flatpak**, and **`CHECKSUMS.sha256`** to the release page. See [docs/DISTRIBUTION.md](docs/DISTRIBUTION.md#ci-release-builds-github-actions).

```bash
poetry version -s
xml2ustx-cli --version
```

Verify downloaded release assets with the checksum file — see [Distribution](#distribution).

---

## Distribution

Install paths (pipx, pre-built GUI/sidecar, Poetry), CI build matrix, checksum verification, code-signing notes, and sidecar install paths are documented in **[docs/DISTRIBUTION.md](docs/DISTRIBUTION.md)**.

---

## Limitations

**There are many limitations.**

- No support for dynamics or volume changes in the score
- No support for swing annotations
- Gradual tempo: basic support for MuseScore `rit.` and `accel.` only
- Tempos assumed to be quarter-note based
- Lyrics must be defined on **all voices** on **all tracks** — no guessing from other staves
- Lyrics spanning multiple notes or tied notes are not handled gracefully
- Lyrics split across notes are phonemized as separate “words” (OpenUtau phonemizer limitation)

---

## Project layout (reference)

| Path | Purpose |
|------|---------|
| `xml2ustx-cli` | Installed CLI command (`src.application.cli_entrypoint`) |
| `xml2ustx` | Installed GUI command (`src.ui.native.gui_entrypoint`) |
| `main.py` | Legacy CLI entry (prefer `xml2ustx-cli`) |
| `native_ui.py` | Legacy GUI entry (prefer `xml2ustx`) |
| `src/resources/config.yml` | Default voice/track presets |
| `tests/fixtures/minimal.musicxml` | Small MusicXML fixture for integration tests |
| `docs/DISTRIBUTION.md` | Release verification, signing, session log paths |
| `xml2ustx.spec` | PyInstaller spec (CLI sidecar) |
| `xml2ustx-gui.spec` | PyInstaller spec (GUI app) |
| `scripts/build_sidecar.sh` | Local sidecar build |
| `scripts/test_integration.sh` | CLI + sidecar smoke tests |
| `scripts/ci/smoke_sidecar.sh` | Smoke-test a packaged sidecar zip |
| `.github/workflows/test.yml` | CI: ruff, pytest matrix, sidecar smoke |
| `.github/workflows/release.yml` | Release builds + checksum upload |
| `integration/openutau/` | OpenUtau Lunai fork patch kit |
