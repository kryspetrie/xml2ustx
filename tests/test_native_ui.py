"""Tests for the native Qt UI."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from PySide6.QtWidgets import QMessageBox

from src.ui.native.app_icon import load_app_icon
from src.ui.native.config_tab import ConfigTab
from src.ui.native.convert_tab import ConvertTab
from src.ui.native.constants import is_supported_input
from src.ui.native.config_store import shipped_config_text
from tests.conftest import MINIMAL_XML


@pytest.fixture
def config_tab(qtbot):
    widget = ConfigTab()
    qtbot.addWidget(widget)
    return widget


@pytest.fixture
def convert_tab(qtbot, config_tab, tmp_path):
    widget = ConvertTab(config_tab.config_file_path)
    qtbot.addWidget(widget)
    return widget


def test_config_tab_starts_clean(config_tab: ConfigTab) -> None:
    assert config_tab.is_dirty() is False


def test_config_tab_marks_dirty_on_edit(config_tab: ConfigTab, qtbot) -> None:
    config_tab.editor_tabs.setCurrentIndex(1)
    config_tab.config_editor.insertPlainText('\n# test')
    qtbot.waitUntil(config_tab.is_dirty)
    assert config_tab.is_dirty() is True


def test_config_tab_has_visual_and_source_editors(config_tab: ConfigTab) -> None:
    assert config_tab.editor_tabs.count() == 2
    assert config_tab.editor_tabs.tabText(0) == 'Visual editor'
    assert config_tab.editor_tabs.tabText(1) == 'Edit file'


def test_config_tab_visual_edit_marks_dirty(config_tab: ConfigTab, qtbot) -> None:
    config_tab.form_editor.default_lyric.setText('la')
    qtbot.waitUntil(config_tab.is_dirty)
    assert config_tab.is_dirty() is True


def test_config_tab_syncs_visual_to_source(config_tab: ConfigTab) -> None:
    config_tab.form_editor.default_lyric.setText('mm')
    config_tab.editor_tabs.setCurrentIndex(1)
    assert 'default_lyric: mm' in config_tab.config_editor.toPlainText()


def test_config_tab_reload_populates_both_editors(config_tab: ConfigTab) -> None:
    text = shipped_config_text()
    config_tab._set_editor_text(text)
    assert config_tab.config_editor.toPlainText() == text
    assert config_tab.form_editor.default_lyric.text() == 'doo'


def test_app_icon_loads() -> None:
    icon = load_app_icon()
    assert not icon.isNull()


def test_convert_tab_collect_requires_input(convert_tab: ConvertTab) -> None:
    with pytest.raises(ValueError, match='Add at least one input file'):
        convert_tab.collect_options()


def test_convert_tab_collect_single_file(convert_tab: ConvertTab, minimal_xml: Path) -> None:
    convert_tab.mode_single.setChecked(True)
    convert_tab.file_list.addItem(str(minimal_xml))
    options = convert_tab.collect_options()
    assert options.input_files == [str(minimal_xml)]
    assert options.open_in_openutau is False


def test_convert_tab_custom_tracks_require_row(convert_tab: ConvertTab, minimal_xml: Path) -> None:
    convert_tab.mode_single.setChecked(True)
    convert_tab.file_list.addItem(str(minimal_xml))
    convert_tab.custom_tracks.setChecked(True)
    while convert_tab.track_model.rowCount():
        convert_tab.track_model.remove_row(0)
    with pytest.raises(ValueError, match='Add at least one custom track row'):
        convert_tab.collect_options()


def test_convert_tab_open_utau_option(convert_tab: ConvertTab, minimal_xml: Path, tmp_path: Path) -> None:
    binary = tmp_path / 'OpenUtau'
    binary.write_text('', encoding='utf-8')
    binary.chmod(0o755)

    convert_tab.mode_single.setChecked(True)
    convert_tab.file_list.addItem(str(minimal_xml))
    convert_tab.open_utau_box.setChecked(True)
    convert_tab._settings.set_str('openutau_path', str(binary))
    options = convert_tab.collect_options()
    assert options.open_in_openutau is True
    assert options.openutau_path == str(binary)


def test_convert_tab_open_utau_requires_configured_path(convert_tab: ConvertTab, minimal_xml: Path) -> None:
    convert_tab.mode_single.setChecked(True)
    convert_tab.file_list.addItem(str(minimal_xml))
    convert_tab.open_utau_box.setChecked(True)
    convert_tab._settings.set_str('openutau_path', '')

    with pytest.raises(ValueError, match='Set the OpenUtau path'):
        convert_tab.collect_options()


def test_ensure_saved_cancel(config_tab: ConfigTab, qtbot, monkeypatch) -> None:
    config_tab.config_editor.insertPlainText('\n# edit')
    qtbot.waitUntil(config_tab.is_dirty)

    monkeypatch.setattr(
        QMessageBox,
        'question',
        lambda *args, **kwargs: QMessageBox.StandardButton.Cancel,
    )
    assert config_tab.ensure_saved() is False


def test_is_supported_input(minimal_xml: Path) -> None:
    assert is_supported_input(minimal_xml) is True
    assert is_supported_input(minimal_xml.with_suffix('.pdf')) is False


def test_run_job_routes_debug_to_log_fn() -> None:
    from src.application.Xml2UstxRunner import run_job
    from src.domain.models.Job import Job
    from src.application.ConfigParser import parse as parse_config
    from src.application.ConfigPaths import resolve_config_file

    config = parse_config(resolve_config_file(None))
    track = config.track_config_map['default'][0]
    job = Job(
        input_files=[str(MINIMAL_XML)],
        output_files=['/tmp/test-ui-log.ustx'],
        name='Test',
        track_configs=[track],
        default_lyric='doo',
        debug=True,
    )
    messages: list[str] = []

    with patch('src.application.Xml2UstxRunner.export_ustx_file') as export_mock:
        export_mock.return_value = None
        with patch('src.application.Xml2UstxRunner.parse_project') as parse_mock:
            parse_mock.return_value = object()
            run_job(job, log_fn=messages.append)

    assert any('Running job with the following config' in line for line in messages)
