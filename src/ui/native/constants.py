"""Shared constants for the native Qt UI."""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QMimeData

INPUT_EXTENSIONS = {'.xml', '.musicxml', '.mxl', '.mid', '.midi'}
INPUT_FILTER = 'MusicXML / MIDI (*.xml *.musicxml *.mxl *.mid *.midi)'
CONFIG_FILTER = 'YAML config (*.yml *.yaml)'
USTX_FILTER = 'USTX project (*.ustx)'


def is_supported_input(path: Path) -> bool:
    """Return ``True`` when ``path`` is a supported input file."""
    return path.is_file() and path.suffix.lower() in INPUT_EXTENSIONS


def paths_from_mime(mime: QMimeData) -> list[str]:
    """Extract local file paths with supported extensions or directories from mime data."""
    if not mime.hasUrls():
        return []
    paths: list[str] = []
    for url in mime.urls():
        if not url.isLocalFile():
            continue
        path = Path(url.toLocalFile())
        if path.is_dir() or is_supported_input(path):
            paths.append(str(path))
    return paths


def mime_has_supported_paths(mime: QMimeData) -> bool:
    """Return ``True`` when mime data contains at least one supported drop target."""
    return bool(paths_from_mime(mime))
