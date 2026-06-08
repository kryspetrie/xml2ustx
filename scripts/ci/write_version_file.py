#!/usr/bin/env python3
"""Bake the current semver into src/application/_version.py for frozen builds."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "src" / "application" / "_version.py"


def read_version() -> str:
    env = os.environ.get("XML2USTX_VERSION", "").strip()
    if env:
        return env

    try:
        return subprocess.check_output(
            ["poetry", "version", "-s"],
            cwd=ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        pass

    try:
        tag = subprocess.check_output(
            ["git", "describe", "--tags", "--match", "v[0-9]*", "--abbrev=0"],
            cwd=ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        return "0.0.0"

    return tag.removeprefix("v")


def main() -> int:
    version = read_version()
    OUT.write_text(f'__version__ = "{version}"\n', encoding="utf-8")
    print(version)
    return 0


if __name__ == "__main__":
    sys.exit(main())
