"""Persistent UI settings via QSettings."""
from __future__ import annotations

from PySide6.QtCore import QSettings
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QMainWindow, QWidget

from src.ui.native.theme import THEME_SYSTEM, normalize_theme
from src.ui.native.window_constraints import (
    DEFAULT_MAIN_WINDOW_HEIGHT,
    DEFAULT_MAIN_WINDOW_WIDTH,
    clamp_main_window_size,
)


class UiSettings:
    """Read/write native UI preferences."""

    def __init__(self, settings: QSettings | None = None):
        self._settings = settings or QSettings('xml2ustx', 'native-ui')

    @property
    def qsettings(self) -> QSettings:
        return self._settings

    def restore_window(self, window: QMainWindow) -> None:
        """Restore window geometry, falling back when off-screen or too small."""
        geometry = self._settings.value('geometry')
        if geometry is not None:
            window.restoreGeometry(geometry)
        clamp_main_window_size(window)
        if not _is_window_visible(window):
            window.resize(DEFAULT_MAIN_WINDOW_WIDTH, DEFAULT_MAIN_WINDOW_HEIGHT)
            window.move(100, 100)

    def save_window(self, window: QMainWindow) -> None:
        """Persist window geometry."""
        self._settings.setValue('geometry', window.saveGeometry())

    def get_str(self, key: str, default: str = '') -> str:
        value = self._settings.value(key)
        return str(value) if value is not None else default

    def get_bool(self, key: str, default: bool = False) -> bool:
        value = self._settings.value(key)
        if value is None:
            return default
        return str(value).lower() in {'1', 'true', 'yes'}

    def set_bool(self, key: str, value: bool) -> None:
        self._settings.setValue(key, value)

    def set_str(self, key: str, value: str) -> None:
        self._settings.setValue(key, value)

    def get_int(self, key: str, default: int = 0) -> int:
        value = self._settings.value(key)
        if value is None:
            return default
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    def set_int(self, key: str, value: int) -> None:
        self._settings.setValue(key, value)

    def get_theme(self) -> str:
        """Return the saved UI theme preference."""
        return normalize_theme(self.get_str('theme', THEME_SYSTEM))

    def set_theme(self, theme: str) -> None:
        """Persist the UI theme preference."""
        self.set_str('theme', normalize_theme(theme))

    def get_openutau_path(self) -> str:
        """Return the saved OpenUtau executable path."""
        return self.get_str('openutau_path')

    def set_openutau_path(self, path: str) -> None:
        """Persist the OpenUtau executable path."""
        self.set_str('openutau_path', path)

    def sync(self) -> None:
        """Flush pending settings to disk."""
        self._settings.sync()


def _is_window_visible(window: QWidget) -> bool:
    """Return ``True`` when at least part of the window intersects a screen."""
    frame = window.frameGeometry()
    if not frame.isValid():
        return False
    for screen in QGuiApplication.screens():
        if screen.availableGeometry().intersects(frame):
            return True
    return False
