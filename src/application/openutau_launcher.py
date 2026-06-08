"""Launch OpenUtau with one or more USTX project files."""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

from src.application.conversion_log import LogFn, emit_log

OPENUTAU_PATH_ENV = 'OPENUTAU_PATH'
MACOS_DEFAULT_APP = Path('/Applications/OpenUtau.app')


def is_macos_app_bundle(path: Path) -> bool:
    """Return ``True`` when ``path`` is a macOS ``.app`` bundle directory."""
    return sys.platform == 'darwin' and path.suffix == '.app' and path.is_dir()


def resolve_macos_app_executable(app_bundle: Path) -> Path | None:
    """Return the main executable inside a macOS ``.app`` bundle."""
    if not is_macos_app_bundle(app_bundle):
        return None

    for name in ('OpenUtau', 'openutau'):
        candidate = app_bundle / 'Contents' / 'MacOS' / name
        if candidate.is_file():
            return candidate

    macos_dir = app_bundle / 'Contents' / 'MacOS'
    if macos_dir.is_dir():
        for child in sorted(macos_dir.iterdir()):
            if child.is_file() and os.access(child, os.X_OK):
                return child

    return None


def is_valid_openutau_path(path: str) -> bool:
    """Return ``True`` when ``path`` points at a launchable OpenUtau install."""
    cleaned = path.strip()
    if not cleaned:
        return False

    candidate = Path(cleaned).expanduser()
    if not candidate.exists():
        return False

    if is_macos_app_bundle(candidate):
        executable = resolve_macos_app_executable(candidate)
        return executable is not None and os.access(executable, os.X_OK)

    if candidate.suffix == '.AppImage' and candidate.is_file():
        return True

    return candidate.is_file()


def openutau_launch_command(configured_path: str, ustx_path: Path) -> list[str] | None:
    """Build the argv used to hand a USTX file to OpenUtau."""
    cleaned = configured_path.strip()
    if not cleaned:
        return None

    candidate = Path(cleaned).expanduser()
    if sys.platform == 'darwin' and is_macos_app_bundle(candidate):
        return ['open', '-a', str(candidate.resolve()), str(ustx_path.resolve())]

    executable = resolve_openutau_executable(cleaned, allow_env_fallback=False)
    if executable is None:
        return None

    return [str(executable), str(ustx_path.resolve())]


def resolve_openutau_executable(
    explicit_path: str | None = None,
    *,
    allow_env_fallback: bool = True,
) -> Path | None:
    """Return the OpenUtau binary, or None if it cannot be found."""
    candidates: list[Path] = []

    if explicit_path:
        expanded = Path(explicit_path).expanduser()
        candidates.append(expanded)
        if is_macos_app_bundle(expanded):
            app_executable = resolve_macos_app_executable(expanded)
            if app_executable is not None:
                candidates.append(app_executable)
    if not allow_env_fallback:
        for candidate in candidates:
            if candidate.is_file() and os.access(candidate, os.X_OK):
                return candidate.resolve()
            if candidate.suffix == '.AppImage' and candidate.is_file():
                return candidate.resolve()
        return None

    env_path = os.environ.get(OPENUTAU_PATH_ENV, '').strip()
    if env_path:
        candidates.append(Path(env_path).expanduser())

    for name in ('OpenUtau', 'openutau'):
        found = shutil.which(name)
        if found:
            candidates.append(Path(found))

    if sys.platform == 'darwin':
        candidates.append(MACOS_DEFAULT_APP)
        app_executable = resolve_macos_app_executable(MACOS_DEFAULT_APP)
        if app_executable is not None:
            candidates.append(app_executable)
    elif sys.platform == "win32":
        local = os.environ.get("LOCALAPPDATA", "")
        if local:
            candidates.extend(
                Path(local, "Programs", "OpenUtau", name)
                for name in ("OpenUtau.exe", "OpenUtau")
            )
        candidates.append(Path(os.environ.get("ProgramFiles", ""), "OpenUtau", "OpenUtau.exe"))
    else:
        candidates.extend(
            Path(path)
            for path in (
                "~/.local/bin/OpenUtau",
                "/usr/bin/OpenUtau",
                "/usr/local/bin/OpenUtau",
            )
        )

    for candidate in candidates:
        if is_macos_app_bundle(candidate):
            app_executable = resolve_macos_app_executable(candidate)
            if app_executable is not None and os.access(app_executable, os.X_OK):
                return app_executable.resolve()
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return candidate.resolve()
        if candidate.suffix == '.AppImage' and candidate.is_file():
            return candidate.resolve()

    return None


def open_in_openutau(
    ustx_files: list[str],
    *,
    openutau_path: str | None = None,
    allow_env_fallback: bool = True,
    log_fn: LogFn | None = None,
) -> bool:
    """Open each USTX file in OpenUtau (one process per file).

    Returns:
        ``True`` when at least one file was handed to OpenUtau successfully.
    """
    if not ustx_files:
        return False

    configured_path = (openutau_path or '').strip()
    if not allow_env_fallback and configured_path and not is_valid_openutau_path(configured_path):
        configured_path = ''

    executable = resolve_openutau_executable(
        openutau_path,
        allow_env_fallback=allow_env_fallback,
    )
    if executable is None and not (
        sys.platform == 'darwin'
        and configured_path
        and is_macos_app_bundle(Path(configured_path).expanduser())
    ):
        if allow_env_fallback:
            emit_log(
                'Could not find OpenUtau. Set OPENUTAU_PATH or specify the OpenUtau binary path.',
                log_fn=log_fn,
                err=log_fn is None,
            )
            emit_log('OpenUtau is not on PATH by default.', log_fn=log_fn, err=log_fn is None)
        else:
            emit_log(
                'Could not find OpenUtau. Set the OpenUtau path in File → Set OpenUtau path…',
                log_fn=log_fn,
                err=log_fn is None,
            )
        for ustx in ustx_files:
            ustx_path = Path(ustx).resolve()
            emit_log(f'  ~/OpenUtau-linux-x64/OpenUtau "{ustx_path}"', log_fn=log_fn, err=log_fn is None)
        emit_log('Or open the file manually in OpenUtau: File → Open', log_fn=log_fn, err=log_fn is None)
        return False

    opened = False
    for ustx in ustx_files:
        ustx_path = Path(ustx).resolve()
        if not ustx_path.is_file():
            emit_log(f'Output file not found, skipping open: {ustx_path}', log_fn=log_fn, err=log_fn is None)
            continue
        launch_command = None
        if configured_path:
            launch_command = openutau_launch_command(configured_path, ustx_path)
        if launch_command is None and executable is not None:
            launch_command = [str(executable), str(ustx_path.resolve())]
        if launch_command is None:
            emit_log(f'Failed to launch OpenUtau for {ustx_path}', log_fn=log_fn, err=log_fn is None)
            continue

        try:
            subprocess.Popen(
                launch_command,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
            emit_log(f'Opened in OpenUtau: {ustx_path}', log_fn=log_fn)
            opened = True
        except OSError as exc:
            emit_log(f'Failed to launch OpenUtau for {ustx_path}: {exc}', log_fn=log_fn, err=log_fn is None)

    return opened
