"""Main window integration tests."""
from __future__ import annotations

import pytest
from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QDialog, QLabel, QMessageBox

from src.ui.native.main_window import PROJECT_GITHUB_URL, MainWindow
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


def test_about_dialog_includes_github_link(main_window: MainWindow, monkeypatch) -> None:
    captured: dict[str, str] = {}

    def _exec(self) -> int:
        label = self.findChild(QLabel)
        captured['text'] = label.text() if label is not None else ''
        return int(QDialog.DialogCode.Accepted)

    monkeypatch.setattr(QDialog, 'exec', _exec, raising=False)
    main_window._show_about()
    assert PROJECT_GITHUB_URL in captured['text']
    assert 'Project on GitHub' in captured['text']


def test_view_menu_opens_conversion_log_window(main_window: MainWindow, qtbot) -> None:
    main_window._show_log_window()
    assert main_window._log_window is not None
    qtbot.waitUntil(main_window._log_window.isVisible)
    main_window.convert_tab.log_line('hello from test')
    assert 'hello from test' in main_window._log_window._editor.toPlainText()
