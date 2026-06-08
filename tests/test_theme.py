"""Tests for UI theme helpers and persisted preferences."""
from __future__ import annotations

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication

from src.ui.native.theme import THEME_DARK, THEME_LIGHT, THEME_SYSTEM, apply_theme, normalize_theme
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
