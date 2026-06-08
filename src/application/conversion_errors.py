"""Structured errors for conversion jobs (CLI, UI, automation)."""
from __future__ import annotations


class ConversionError(Exception):
    """Base error for conversion failures with a stable machine-readable code."""

    code: str = 'conversion_error'

    def __init__(self, message: str, *, code: str | None = None):
        super().__init__(message)
        if code is not None:
            self.code = code

    def formatted(self) -> str:
        """Return a user-facing message including the error code."""
        return f'[{self.code}] {self}'


class ConversionCancelledError(ConversionError):
    """Raised when a conversion job is cancelled cooperatively."""

    code = 'cancelled'


class ConversionInputError(ConversionError):
    """Raised when user input or configuration is invalid."""

    code = 'invalid_input'


class ConversionExportError(ConversionError):
    """Raised when USTX export fails."""

    code = 'export_failed'
