"""Installed console entry point for the xml2ustx CLI."""
from __future__ import annotations

import sys

from src.application.conversion_errors import ConversionError
from src.application.Xml2UstxRunner import run_cli


def main() -> None:
    """Run the xml2ustx command-line interface."""
    try:
        run_cli()
    except ConversionError as exc:
        print(exc.formatted(), file=sys.stderr)
        sys.exit(1)
    except Exception as exc:
        print(exc, file=sys.stderr)
        sys.exit(1)
