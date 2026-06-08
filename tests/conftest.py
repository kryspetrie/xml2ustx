"""Shared pytest fixtures."""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURES_DIR = Path(__file__).resolve().parent / 'fixtures'
MINIMAL_XML = FIXTURES_DIR / 'minimal.musicxml'
DEFAULT_CONFIG = REPO_ROOT / 'src' / 'resources' / 'config.yml'
CLI_COMMAND = 'xml2ustx-cli'


@pytest.fixture
def repo_root() -> Path:
    """Return the repository root directory."""
    return REPO_ROOT


@pytest.fixture
def fixtures_dir() -> Path:
    """Return the ``tests/fixtures`` directory."""
    return FIXTURES_DIR


@pytest.fixture
def minimal_xml() -> Path:
    """Return the minimal MusicXML fixture path."""
    return MINIMAL_XML


@pytest.fixture
def default_config() -> Path:
    """Return the bundled default ``config.yml`` path."""
    return DEFAULT_CONFIG


@pytest.fixture
def cli_runner(repo_root: Path):
    """Return a helper that invokes the installed ``xml2ustx-cli`` console script."""

    def run(*args: str, check: bool = False) -> subprocess.CompletedProcess[str]:
        command = [shutil.which(CLI_COMMAND) or str(repo_root / 'main.py'), *args]
        if command[0].endswith('main.py'):
            command = [sys.executable, *command]
        return subprocess.run(
            command,
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=check,
        )

    return run
