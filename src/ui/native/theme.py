"""Application theme helpers for the native UI."""
from __future__ import annotations

import subprocess
import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication, QPalette, QColor
from PySide6.QtWidgets import QApplication, QStyleFactory, QWidget

from src.ui.native.application_style import apply_application_style

THEME_SYSTEM = 'system'
THEME_LIGHT = 'light'
THEME_DARK = 'dark'
VALID_THEMES = frozenset({THEME_SYSTEM, THEME_LIGHT, THEME_DARK})

THEME_LABELS = {
    THEME_SYSTEM: 'System default',
    THEME_LIGHT: 'Light',
    THEME_DARK: 'Dark',
}

_LIGHT_COLORS: dict[QPalette.ColorRole, tuple[int, int, int]] = {
    QPalette.ColorRole.Window: (239, 239, 239),
    QPalette.ColorRole.WindowText: (0, 0, 0),
    QPalette.ColorRole.Base: (255, 255, 255),
    QPalette.ColorRole.AlternateBase: (233, 233, 233),
    QPalette.ColorRole.ToolTipBase: (255, 255, 220),
    QPalette.ColorRole.ToolTipText: (0, 0, 0),
    QPalette.ColorRole.Text: (0, 0, 0),
    QPalette.ColorRole.Button: (239, 239, 239),
    QPalette.ColorRole.ButtonText: (0, 0, 0),
    QPalette.ColorRole.BrightText: (255, 0, 0),
    QPalette.ColorRole.Link: (0, 0, 255),
    QPalette.ColorRole.Highlight: (42, 130, 218),
    QPalette.ColorRole.HighlightedText: (255, 255, 255),
}

_DARK_COLORS: dict[QPalette.ColorRole, tuple[int, int, int]] = {
    QPalette.ColorRole.Window: (53, 53, 53),
    QPalette.ColorRole.WindowText: (255, 255, 255),
    QPalette.ColorRole.Base: (25, 25, 25),
    QPalette.ColorRole.AlternateBase: (53, 53, 53),
    QPalette.ColorRole.ToolTipBase: (255, 255, 220),
    QPalette.ColorRole.ToolTipText: (0, 0, 0),
    QPalette.ColorRole.Text: (255, 255, 255),
    QPalette.ColorRole.Button: (53, 53, 53),
    QPalette.ColorRole.ButtonText: (255, 255, 255),
    QPalette.ColorRole.BrightText: (255, 0, 0),
    QPalette.ColorRole.Link: (42, 130, 218),
    QPalette.ColorRole.Highlight: (42, 130, 218),
    QPalette.ColorRole.HighlightedText: (255, 255, 255),
}

_SYSTEM_THEME_CONNECTION = '_xml2ustx_system_theme_connection'


def normalize_theme(value: str | None) -> str:
    """Return a supported theme id, falling back to the system default."""
    if value in VALID_THEMES:
        return value
    return THEME_SYSTEM


def detect_system_color_scheme() -> Qt.ColorScheme:
    """Detect the desktop light/dark preference."""
    desktop = _linux_desktop_color_scheme()
    if desktop is not None:
        return desktop

    hints = QGuiApplication.styleHints()
    qt_scheme = hints.colorScheme()
    if qt_scheme in (Qt.ColorScheme.Light, Qt.ColorScheme.Dark):
        return qt_scheme

    return Qt.ColorScheme.Light


def apply_theme(app: QApplication, theme: str) -> None:
    """Apply light, dark, or system-native color scheme to the application."""
    normalized = normalize_theme(theme)
    app.setProperty('xml2ustx_theme', normalized)

    if normalized == THEME_SYSTEM:
        app.setStyle(_platform_style_name())
        QGuiApplication.styleHints().setColorScheme(Qt.ColorScheme.Unknown)
        scheme = detect_system_color_scheme()
    else:
        app.setStyle('Fusion')
        scheme = (
            Qt.ColorScheme.Light
            if normalized == THEME_LIGHT
            else Qt.ColorScheme.Dark
        )
        QGuiApplication.styleHints().setColorScheme(scheme)

    app.setPalette(_palette_for_color_scheme(scheme))
    app.setProperty(
        'xml2ustx_resolved_scheme',
        'dark' if scheme == Qt.ColorScheme.Dark else 'light',
    )
    apply_application_style(app)
    _refresh_widget_tree(app)
    _ensure_system_theme_listener(app)


def bind_system_theme_updates(app: QApplication) -> None:
    """Re-apply the system theme when the OS color scheme changes."""
    _ensure_system_theme_listener(app)


def _linux_desktop_color_scheme() -> Qt.ColorScheme | None:
    if sys.platform not in {'linux', 'linux2'}:
        return None

    gtk_theme = _read_gsettings(
        'org.gnome.desktop.interface',
        'gtk-theme',
    )
    if gtk_theme:
        lowered = gtk_theme.lower()
        if 'dark' in lowered:
            return Qt.ColorScheme.Dark
        return Qt.ColorScheme.Light

    color_scheme = _read_gsettings(
        'org.gnome.desktop.interface',
        'color-scheme',
    )
    if color_scheme == 'prefer-dark':
        return Qt.ColorScheme.Dark
    if color_scheme in {'prefer-light', 'default'}:
        return Qt.ColorScheme.Light

    return None


def _read_gsettings(schema: str, key: str) -> str | None:
    try:
        output = subprocess.check_output(
            ['gsettings', 'get', schema, key],
            text=True,
            timeout=1,
            stderr=subprocess.DEVNULL,
        )
    except (OSError, subprocess.SubprocessError):
        return None

    value = output.strip()
    if value in {'', "''"}:
        return None
    if value.startswith("'") and value.endswith("'"):
        return value[1:-1]
    return value


def _platform_style_name() -> str:
    keys = QStyleFactory.keys()
    if sys.platform == 'darwin':
        for name in ('macOS', 'Macintosh'):
            if name in keys:
                return name
    elif sys.platform == 'win32':
        for name in ('windowsvista', 'Windows11', 'Windows'):
            if name in keys:
                return name
    return 'Fusion'


def _palette_for_color_scheme(scheme: Qt.ColorScheme) -> QPalette:
    if scheme == Qt.ColorScheme.Dark:
        return _build_palette(_DARK_COLORS)
    return _build_palette(_LIGHT_COLORS)


def _build_palette(colors: dict[QPalette.ColorRole, tuple[int, int, int]]) -> QPalette:
    palette = QPalette()
    for role, rgb in colors.items():
        color = QColor(*rgb)
        palette.setColor(QPalette.ColorGroup.All, role, color)
        if role in (
            QPalette.ColorRole.WindowText,
            QPalette.ColorRole.Text,
            QPalette.ColorRole.ButtonText,
            QPalette.ColorRole.Highlight,
            QPalette.ColorRole.HighlightedText,
        ):
            disabled = QColor(color)
            disabled.setAlpha(128)
            palette.setColor(QPalette.ColorGroup.Disabled, role, disabled)
    return palette


def _refresh_widget_tree(app: QApplication) -> None:
    """Push the application palette through the live widget tree."""
    palette = app.palette()
    style = app.style()
    for widget in app.allWidgets():
        _refresh_widget(widget, palette, style)

    for widget in app.topLevelWidgets():
        widget.repaint()


def _refresh_widget(widget: QWidget, palette: QPalette, style) -> None:
    widget.setPalette(palette)
    style.unpolish(widget)
    style.polish(widget)
    widget.update()


def _ensure_system_theme_listener(app: QApplication) -> None:
    hints = QGuiApplication.styleHints()
    existing = app.property(_SYSTEM_THEME_CONNECTION)
    if existing is not None:
        try:
            hints.colorSchemeChanged.disconnect(existing)
        except (RuntimeError, TypeError):
            pass

    def _on_system_scheme_changed(_scheme: Qt.ColorScheme) -> None:
        if app.property('xml2ustx_theme') != THEME_SYSTEM:
            return
        apply_theme(app, THEME_SYSTEM)

    hints.colorSchemeChanged.connect(_on_system_scheme_changed)
    app.setProperty(_SYSTEM_THEME_CONNECTION, _on_system_scheme_changed)


def fusion_standard_palette() -> QPalette:
    """Return Fusion's built-in standard palette (used in tests)."""
    style = QStyleFactory.create('Fusion')
    if style is None:
        return QPalette()
    return style.standardPalette()
