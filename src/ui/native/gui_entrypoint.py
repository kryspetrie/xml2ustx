"""Installed console entry point for the xml2ustx native desktop UI."""
from __future__ import annotations

import sys

from src.ui.native.main_window import run_app


def main() -> None:
    """Launch the Qt6 desktop application."""
    sys.exit(run_app())
