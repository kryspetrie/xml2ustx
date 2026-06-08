"""Main window integration tests."""
from __future__ import annotations

import pytest
from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QMessageBox

from src.ui.native.main_window import MainWindow
from src.ui.native.ui_settings import UiSettings


@pytest.fixture
def main_window(qtbot, monkeypatch):
    settings = UiSettings(QSettings('xml2ustx-test', 'mainwindow-test'))
    monkeypatch.setattr(MainWindow, '_restore_settings', lambda self: None)
    window = MainWindow()
    window._settings = settings
    qtbot.addWidget(window)
    yield window
    window.config_tab._set_dirty(False)
    window.close()


def test_tab_switch_blocked_when_config_dirty(main_window: MainWindow, monkeypatch) -> None:
    monkeypatch.setattr(
        QMessageBox,
        'question',
        lambda *args, **kwargs: QMessageBox.StandardButton.Cancel,
    )
    main_window._tabs.setCurrentIndex(main_window._config_tab_index)
    main_window.config_tab.config_editor.insertPlainText('\n# dirty')
    assert main_window.config_tab.is_dirty()

    main_window._tabs.setCurrentIndex(main_window._convert_tab_index)
    assert main_window._tabs.currentIndex() == main_window._config_tab_index


def test_tab_switch_allowed_when_config_clean(main_window: MainWindow) -> None:
    main_window._tabs.setCurrentIndex(main_window._config_tab_index)
    main_window._tabs.setCurrentIndex(main_window._convert_tab_index)
    assert main_window._tabs.currentIndex() == main_window._convert_tab_index
