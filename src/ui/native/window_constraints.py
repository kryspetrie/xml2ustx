"""Main window size constraints for the native UI."""
from __future__ import annotations

from PySide6.QtWidgets import QMainWindow

MIN_MAIN_WINDOW_WIDTH = 960
MIN_MAIN_WINDOW_HEIGHT = 960

DEFAULT_MAIN_WINDOW_WIDTH = MIN_MAIN_WINDOW_WIDTH
DEFAULT_MAIN_WINDOW_HEIGHT = MIN_MAIN_WINDOW_HEIGHT


def apply_main_window_constraints(window: QMainWindow) -> None:
    """Apply minimum size limits to the primary application window."""
    window.setMinimumSize(MIN_MAIN_WINDOW_WIDTH, MIN_MAIN_WINDOW_HEIGHT)


def clamp_main_window_size(window: QMainWindow) -> None:
    """Grow the window to at least the enforced minimum size."""
    min_width = window.minimumWidth()
    min_height = window.minimumHeight()
    width = max(window.width(), min_width)
    height = max(window.height(), min_height)
    if width != window.width() or height != window.height():
        window.resize(width, height)
