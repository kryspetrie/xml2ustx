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


def test_restore_window_clamps_below_minimum(qtbot) -> None:
    from src.ui.native.window_constraints import (
        MIN_MAIN_WINDOW_HEIGHT,
        MIN_MAIN_WINDOW_WIDTH,
        apply_main_window_constraints,
    )

    window = QMainWindow()
    qtbot.addWidget(window)
    apply_main_window_constraints(window)
    window.resize(640, 480)

    settings = UiSettings(QSettings('xml2ustx-test', 'window-clamp-test'))
    settings.save_window(window)
    window.resize(400, 300)

    settings.restore_window(window)
    assert window.width() >= MIN_MAIN_WINDOW_WIDTH
    assert window.height() >= MIN_MAIN_WINDOW_HEIGHT
