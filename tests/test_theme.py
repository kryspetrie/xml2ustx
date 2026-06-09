"""Tests for UI theme helpers and persisted preferences."""
from __future__ import annotations

from PySide6.QtCore import QSettings, Qt
from PySide6.QtGui import QPalette
from PySide6.QtWidgets import QApplication, QMessageBox

from src.ui.native.theme import (
    THEME_DARK,
    THEME_LIGHT,
    THEME_SYSTEM,
    apply_theme,
    detect_system_color_scheme,
    normalize_theme,
)
from src.ui.native.ui_settings import UiSettings


def test_normalize_theme_falls_back_to_system() -> None:
    assert normalize_theme('invalid') == THEME_SYSTEM
    assert normalize_theme(THEME_DARK) == THEME_DARK


def test_ui_settings_theme_round_trip() -> None:
    settings = UiSettings(QSettings('xml2ustx-test', 'theme-test'))
    settings.set_theme(THEME_DARK)
    settings.sync()

    assert settings.get_theme() == THEME_DARK


def test_ui_settings_openutau_path_round_trip() -> None:
    settings = UiSettings(QSettings('xml2ustx-test', 'openutau-test'))
    settings.set_openutau_path('/Applications/OpenUtau.app')
    settings.sync()

    assert settings.get_openutau_path() == '/Applications/OpenUtau.app'


def test_apply_theme_records_selected_theme() -> None:
    app = QApplication.instance() or QApplication([])

    apply_theme(app, THEME_DARK)
    assert app.property('xml2ustx_theme') == THEME_DARK

    apply_theme(app, THEME_LIGHT)
    assert app.property('xml2ustx_theme') == THEME_LIGHT

    apply_theme(app, THEME_SYSTEM)
    assert app.property('xml2ustx_theme') == THEME_SYSTEM


def test_apply_theme_changes_window_palette() -> None:
    app = QApplication.instance() or QApplication([])

    apply_theme(app, THEME_LIGHT)
    light = app.palette().color(QPalette.ColorRole.Window)
    light_rgb = (light.red(), light.green(), light.blue())

    apply_theme(app, THEME_DARK)
    dark = app.palette().color(QPalette.ColorRole.Window)
    dark_rgb = (dark.red(), dark.green(), dark.blue())

    assert light_rgb != dark_rgb
    assert light_rgb == (239, 239, 239)
    assert dark_rgb == (53, 53, 53)


def test_apply_theme_refreshes_existing_widgets() -> None:
    from PySide6.QtWidgets import QPushButton

    app = QApplication.instance() or QApplication([])
    button = QPushButton('Theme test')
    button.show()

    apply_theme(app, THEME_LIGHT)
    apply_theme(app, THEME_DARK)

    window = button.palette().color(QPalette.ColorRole.Window)
    window_rgb = (window.red(), window.green(), window.blue())
    assert window_rgb == (53, 53, 53)


def test_detect_system_color_scheme_uses_linux_desktop_preference(monkeypatch) -> None:
    monkeypatch.setattr(
        'src.ui.native.theme._linux_desktop_color_scheme',
        lambda: Qt.ColorScheme.Light,
    )
    assert detect_system_color_scheme() == Qt.ColorScheme.Light

    monkeypatch.setattr(
        'src.ui.native.theme._linux_desktop_color_scheme',
        lambda: Qt.ColorScheme.Dark,
    )
    assert detect_system_color_scheme() == Qt.ColorScheme.Dark


def test_apply_system_theme_follows_desktop_preference(monkeypatch) -> None:
    app = QApplication.instance() or QApplication([])

    monkeypatch.setattr(
        'src.ui.native.theme._linux_desktop_color_scheme',
        lambda: Qt.ColorScheme.Light,
    )
    apply_theme(app, THEME_DARK)
    apply_theme(app, THEME_SYSTEM)

    assert app.property('xml2ustx_theme') == THEME_SYSTEM
    assert app.property('xml2ustx_resolved_scheme') == 'light'
    window = app.palette().color(QPalette.ColorRole.Window)
    assert (window.red(), window.green(), window.blue()) == (239, 239, 239)


def test_linux_desktop_prefers_gtk_theme_over_color_scheme(monkeypatch) -> None:
    def _read(schema: str, key: str) -> str | None:
        if key == 'gtk-theme':
            return 'Pop-dark'
        if key == 'color-scheme':
            return 'prefer-light'
        return None

    monkeypatch.setattr('src.ui.native.theme._read_gsettings', _read)
    monkeypatch.setattr('src.ui.native.theme.sys.platform', 'linux')

    from src.ui.native.theme import _linux_desktop_color_scheme

    assert _linux_desktop_color_scheme() == Qt.ColorScheme.Dark


def test_application_stylesheet_uses_theme_specific_help_text_color() -> None:
    from src.ui.native.application_style import application_stylesheet

    light = application_stylesheet('light')
    dark = application_stylesheet('dark')

    assert '#424242' in light
    assert 'palette(mid)' not in light
    assert '#CCCCCC' in dark
    assert 'palette(mid)' not in dark
