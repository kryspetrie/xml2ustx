"""Project version (semver from git tags via poetry-dynamic-versioning)."""

from __future__ import annotations

import re
import subprocess
from functools import lru_cache
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SEMVER_TAG = re.compile(
    r"^v(?P<version>\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?)$"
)


@lru_cache(maxsize=1)
def get_version() -> str:
    """Return the current semver string."""
    try:
        from src.application._version import __version__

        return __version__
    except ImportError:
        pass

    poetry = _REPO_ROOT / ".venv" / "bin" / "poetry"
    if poetry.is_file():
        try:
            return subprocess.check_output(
                [str(poetry), "version", "-s"],
                cwd=_REPO_ROOT,
                stderr=subprocess.DEVNULL,
                text=True,
            ).strip()
        except (subprocess.CalledProcessError, OSError):
            pass

    try:
        return subprocess.check_output(
            ["poetry", "version", "-s"],
            cwd=_REPO_ROOT,
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        pass

    return _version_from_git()


def _version_from_git() -> str:
    try:
        describe = subprocess.check_output(
            [
                "git",
                "describe",
                "--tags",
                "--match",
                "v[0-9]*",
                "--long",
                "--dirty",
            ],
            cwd=_REPO_ROOT,
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        return "0.0.0"

    if describe.endswith("-dirty"):
        describe = describe[: -len("-dirty")] + "+dirty"

    if describe.startswith("v"):
        describe = describe[1:]

    # Exact tag: 1.0.0
    match = _SEMVER_TAG.match(f"v{describe.split('-', 1)[0]}")
    if match and "-" not in describe:
        return match.group("version")

    # N commits after tag: 1.0.0-5-gabc1234
    parts = describe.split("-")
    if len(parts) >= 3 and parts[1].isdigit() and parts[2].startswith("g"):
        base = parts[0]
        distance = parts[1]
        commit = parts[2][1:]
        suffix = "+".join(parts[3:]) if len(parts) > 3 else ""
        build = f"{distance}.{commit}"
        if suffix:
            build = f"{build}.{suffix}"
        return f"{base}+{build}"

    return describe


__version__ = get_version()
