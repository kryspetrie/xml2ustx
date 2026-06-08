"""Session logging to file and optional UI/CLI sinks."""
from __future__ import annotations

import os
import sys
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path

from src.application.conversion_log import LogFn, emit_log

LogSink = Callable[[str], None]


def default_log_directory() -> Path:
    """Return the platform-specific directory for session log files."""
    if sys.platform == 'darwin':
        base = Path.home() / 'Library' / 'Logs' / 'xml2ustx'
    elif sys.platform == 'win32':
        local = os.environ.get('LOCALAPPDATA', str(Path.home()))
        base = Path(local) / 'xml2ustx' / 'logs'
    else:
        base = Path.home() / '.local' / 'share' / 'xml2ustx' / 'logs'
    base.mkdir(parents=True, exist_ok=True)
    return base


class SessionLogger:
    """Write timestamped conversion logs to disk and forward to another sink."""

    def __init__(
            self,
            *,
            log_fn: LogFn | None = None,
            log_directory: Path | None = None,
            session_name: str | None = None):
        stamp = datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')
        safe_name = (session_name or 'conversion').replace('/', '_')
        directory = log_directory or default_log_directory()
        self.path = directory / f'{stamp}-{safe_name}.log'
        self._file = self.path.open('a', encoding='utf-8')
        self._log_fn = log_fn

    def write(self, message: str, *, err: bool = False) -> None:
        """Append one log line to the session file and optional sink."""
        line = f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S")} {message}'
        self._file.write(line + '\n')
        self._file.flush()
        emit_log(message, log_fn=self._log_fn, err=err)

    def close(self) -> None:
        """Close the underlying log file."""
        self._file.close()

    def __enter__(self) -> SessionLogger:
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()
