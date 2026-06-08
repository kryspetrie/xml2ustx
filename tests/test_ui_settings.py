"""Tests for UI settings helpers."""
from __future__ import annotations

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QMainWindow

from src.ui.native.ui_settings import UiSettings, _is_window_visible


def test_ui_settings_round_trip(qtbot) -> None:
    settings = UiSettings(QSettings('xml2ustx-test', 'native-ui-test'))
    settings.set_str('project_name', 'My Song')
    settings.set_bool('debug', True)
    settings.set_int('last_tab_index', 1)

    assert settings.get_str('project_name') == 'My Song'
    assert settings.get_bool('debug') is True
    assert settings.get_int('last_tab_index') == 1


def test_window_visibility_check(qtbot) -> None:
    window = QMainWindow()
    qtbot.addWidget(window)
    window.resize(400, 300)
    window.move(50, 50)
    window.show()
    assert _is_window_visible(window) is True
