# MusicXML to USTX

Convert MusicXML (`.mxl`, `.xml`, `.musicxml`, `.midi`) into [OpenUtau](https://github.com/stakira/OpenUtau) `.ustx` projects for singing voice synthesis.

This is a rewrite based on [nicolalandro/xml2ustx](https://github.com/nicolalandro/xml2ustx), with MuseScore-oriented parsing (via [music21](https://web.mit.edu/music21/)), track/voice presets, `.mxl` support, and rit/accel tempo handling.

## Contents

- [Requirements](#requirements)
- [Installation](#installation)
- [CLI application](#cli-application)
- [Configuration](#configuration)
- [Native desktop app](#native-desktop-app)
- [OpenUtau integration](#openutau-integration)
- [Development and testing](#development-and-testing)
- [Releases and versioning](#releases-and-versioning)
- [Distribution](#distribution)
- [MusicXML conversion notes](#musicxml-conversion-notes)

---

## Requirements

Choose one install path below:

| Path | You need |
|------|----------|
| [Pre-built GUI](#pre-built-executables-no-python) | Nothing (download from [GitHub Releases](https://github.com/kryspetrie/xml2ustx/releases)) |
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

`<platform>` is one of: `win-x64`, `win-x86`, `win-arm64`, `linux-x64`, `linux-arm64`, `osx-x64`, `osx-arm64`.

> **Note:** OpenUtau **sidecar** zips are not published in releases yet — the upstream OpenUtau integration that consumes them is still pending. Use the GUI, `pipx`, or `xml2ustx-cli` from source. Sidecar build scripts remain in the repo for future integration work ([`integration/openutau/`](integration/openutau/)).

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

In the native GUI, open **View → Conversion log…** for a live log window with copy/save/clear. See [docs/DISTRIBUTION.md](docs/DISTRIBUTION.md) for release verification and packaging notes.

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
- **Native GUI:** `xml2ustx` then use “Open output folder” or **View → Conversion log…**

Batch mode (`--input_dir --open`) tries to spawn one OpenUtau process per output file (subject to the single-instance limitation above).

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

A patch kit for [OpenUtau-DiffSinger-Lunai](https://github.com/keirokeer/OpenUtau-DiffSinger-Lunai) lives in **[integration/openutau/](integration/openutau/)** (import menu, config editor, sidecar wiring). It is **not** part of published releases yet — upstream OpenUtau builds that ship the integration are still pending.

Until then, convert with the **GUI** or **`xml2ustx-cli`**, then open the `.ustx` in OpenUtau manually.

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

CI (`.github/workflows/test.yml`) runs ruff and pytest on Python 3.12 and 3.13.

### Integration smoke test

```bash
./scripts/test_integration.sh --skip-sidecar-build
```

Sidecar build steps in that script are optional and disabled in CI until OpenUtau integration releases resume.

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

The **Release** workflow (GitHub Actions on `windows-latest`, `ubuntu-latest`, `ubuntu-24.04-arm`, `macos-15-intel`, and `windows-11-arm`) uploads PyInstaller **GUI** zips, a Linux x64 **AppImage**, a Linux x64 **Flatpak**, and **`CHECKSUMS.sha256`** to the release page. See [docs/DISTRIBUTION.md](docs/DISTRIBUTION.md#ci-release-builds-github-actions).

```bash
poetry version -s
xml2ustx-cli --version
```

Verify downloaded release assets with the checksum file — see [Distribution](#distribution).

---

## Distribution

Install paths (pipx, pre-built GUI, Poetry), CI build matrix, checksum verification, and code-signing notes are documented in **[docs/DISTRIBUTION.md](docs/DISTRIBUTION.md)**.

---

## MusicXML conversion notes

| Topic | Behavior |
|-------|----------|
| **Dynamics / volume in score** | `Dynamic` markings and crescendo/diminuendo hairpins export as a `dyn` automation curve on each voice part. Per-note `vol` expressions are set from the nearest preceding dynamic. Track mixer volume still comes from `config.yml`. |
| **Swing / groove** | **Convert** tab: choose **swing** and **groove** presets (or **(None)** to leave groove off), plus **Disable swing/groove**, **Force swing**, and **Force groove**. **Config** tab defines saved preset libraries only. Swing applies when a `Swing` text expression is present (excluding title and lyrics), or when forced. Groove applies when a `Groove` marking is present and a groove preset is selected, or when forced. Optional `Swing 66%` in the score overrides intensity. |
| **Gradual tempo** | MuseScore-style `rit.` and `accel.` with spanner lines are interpolated into stepped tempos. A following metronome mark at the span end is used as the target BPM when present. |
| **Tempo beat unit** | Metronome marks are normalized to quarter-note BPM (e.g. half note = 60 → 120 quarter BPM). |
| **Lyrics** | Score lyrics are used when present. Missing lyrics are copied from other parts at the same beat, then filled from `default_lyric` in config (editable in the UI config tab). Continuation notes use OpenUtau’s `+` lyric. |
| **Tied notes / multi-note lyrics** | Tie chains and begin/middle/end syllable groups are merged onto the first note; continuation notes are marked with `+`. |
| **Other tempo text** | Expressions other than `rit.` and `accel.` are ignored with a warning. |
| **Phonemization** | Merged lyrics are phonemized as one word; `+` continuation notes inherit timing from the merged syllable group. |

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
| `xml2ustx-gui.spec` | PyInstaller spec (GUI app) |
| `scripts/test_integration.sh` | CLI integration smoke test |
| `.github/workflows/test.yml` | CI: ruff, pytest matrix |
| `.github/workflows/release.yml` | Release builds + checksum upload |
| `integration/openutau/` | OpenUtau Lunai fork patch kit |
