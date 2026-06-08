"""Logging helpers for conversion jobs (CLI stdout vs UI log panel)."""
from __future__ import annotations

import sys
from collections.abc import Callable
from typing import TypeAlias

LogFn: TypeAlias = Callable[[str], None]


def emit_log(message: str, *, log_fn: LogFn | None = None, err: bool = False) -> None:
    """Send a log line to a UI sink or stdout/stderr when no sink is provided."""
    if log_fn is not None:
        log_fn(message)
    elif err:
        print(message, file=sys.stderr)
    else:
        print(message)
