"""Application theme helpers for the native UI."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QApplication

THEME_SYSTEM = 'system'
THEME_LIGHT = 'light'
THEME_DARK = 'dark'
VALID_THEMES = frozenset({THEME_SYSTEM, THEME_LIGHT, THEME_DARK})

THEME_LABELS = {
    THEME_SYSTEM: 'System default',
    THEME_LIGHT: 'Light',
    THEME_DARK: 'Dark',
}


def normalize_theme(value: str | None) -> str:
    """Return a supported theme id, falling back to the system default."""
    if value in VALID_THEMES:
        return value
    return THEME_SYSTEM


def apply_theme(app: QApplication, theme: str) -> None:
    """Apply light, dark, or system-native color scheme to the application."""
    normalized = normalize_theme(theme)
    scheme = Qt.ColorScheme.Unknown
    if normalized == THEME_LIGHT:
        scheme = Qt.ColorScheme.Light
    elif normalized == THEME_DARK:
        scheme = Qt.ColorScheme.Dark

    QGuiApplication.styleHints().setColorScheme(scheme)
    app.setProperty('xml2ustx_theme', normalized)
