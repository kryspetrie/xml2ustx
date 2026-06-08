"""Tests for the conversion presenter."""
from __future__ import annotations

import pytest

from src.ui.native.config_tab import ConfigTab
from src.ui.native.conversion_presenter import ConversionPresenter
from src.ui.native.convert_tab import ConvertTab
from src.ui.native.ui_settings import UiSettings


@pytest.fixture
def presenter(qtbot, minimal_xml):
    config_tab = ConfigTab()
    convert_tab = ConvertTab(config_tab.config_file_path, UiSettings())
    qtbot.addWidget(config_tab)
    qtbot.addWidget(convert_tab)
    convert_tab.mode_single.setChecked(True)
    convert_tab.file_list.addItem(str(minimal_xml))
    return ConversionPresenter(convert_tab, config_tab, UiSettings())


def test_presenter_validates_before_start(presenter: ConversionPresenter, qtbot) -> None:
    presenter._convert_tab.file_list.clear()
    with qtbot.waitSignal(presenter.validation_failed, timeout=1000):
        presenter.start_conversion()


def test_presenter_not_busy_initially(presenter: ConversionPresenter) -> None:
    assert presenter.is_busy() is False
