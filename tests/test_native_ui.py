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
    config_tab.editor_tabs.setCurrentIndex(config_tab._SOURCE_TAB)
    config_tab.config_editor.insertPlainText('\n# test')
    qtbot.waitUntil(config_tab.is_dirty)
    assert config_tab.is_dirty() is True


def test_config_tab_has_flat_editor_pages(config_tab: ConfigTab) -> None:
    tabs = config_tab.editor_tabs
    assert tabs.count() == 5
    assert tabs.tabText(0) == 'General'
    assert tabs.tabText(1) == 'Rhythm'
    assert tabs.tabText(2) == 'Voices'
    assert tabs.tabText(3) == 'Tracks'
    assert tabs.tabText(4) == 'Edit file'


def test_config_tab_visual_edit_marks_dirty(config_tab: ConfigTab, qtbot) -> None:
    config_tab.form_editor.default_lyric.setText('la')
    qtbot.waitUntil(config_tab.is_dirty)
    assert config_tab.is_dirty() is True


def test_config_tab_syncs_visual_to_source(config_tab: ConfigTab) -> None:
    config_tab.form_editor.default_lyric.setText('mm')
    config_tab.editor_tabs.setCurrentIndex(config_tab._SOURCE_TAB)
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


def test_convert_tab_rhythm_presets_in_form_state(convert_tab: ConvertTab, minimal_xml: Path) -> None:
    convert_tab.mode_single.setChecked(True)
    convert_tab.file_list.addItem(str(minimal_xml))

    heavy_index = convert_tab.swing_preset.findText('heavy')
    if heavy_index >= 0:
        convert_tab.swing_preset.setCurrentIndex(heavy_index)

    groove_index = convert_tab.groove_preset.findText('eighth-triplet')
    if groove_index >= 0:
        convert_tab.groove_preset.setCurrentIndex(groove_index)

    convert_tab.force_swing.setChecked(True)
    state = convert_tab.form_state()
    options = convert_tab.collect_options()

    if heavy_index >= 0:
        assert state.swing_preset_id == 'heavy'
        assert options.swing_preset_id == 'heavy'
    if groove_index >= 0:
        assert state.groove_preset_id == 'eighth-triplet'
        assert options.groove_preset_id == 'eighth-triplet'
    assert state.force_swing is True
    assert options.force_swing is True


def test_convert_tab_rhythm_disabled_clears_preset_controls(convert_tab: ConvertTab) -> None:
    convert_tab.rhythm_disabled.setChecked(True)
    assert convert_tab.swing_preset.isEnabled() is False
    assert convert_tab.groove_preset.isEnabled() is False
    assert convert_tab.force_swing.isEnabled() is False
    assert convert_tab.force_groove.isEnabled() is False


def test_convert_tab_form_controls_keep_visible_height(convert_tab: ConvertTab, qtbot) -> None:
    convert_tab.resize(960, 960)
    qtbot.wait(10)
    assert convert_tab.project_name.height() > 0
    assert convert_tab.track_preset.height() > 0
    assert convert_tab.swing_preset.height() > 0
    assert convert_tab.groove_preset.height() > 0


def test_convert_tab_uses_two_column_options_layout(convert_tab: ConvertTab, qtbot) -> None:
    assert convert_tab.project_group.parentWidget() is convert_tab._options_left
    assert convert_tab.custom_tracks_group.parentWidget() is convert_tab._options_right
    assert convert_tab.input_group.parentWidget() is convert_tab
    convert_tab.show()
    qtbot.wait(10)
    assert convert_tab._options_right.geometry().x() > convert_tab._options_left.geometry().x()


def test_conversion_log_window_shows_buffered_lines(qtbot) -> None:
    from src.ui.native.conversion_log import ConversionLog, ConversionLogWindow

    log = ConversionLog()
    log.append('first line')
    window = ConversionLogWindow(log)
    qtbot.addWidget(window)
    window.show()

    assert 'first line' in window._editor.toPlainText()
    log.append('second line')
    assert 'second line' in window._editor.toPlainText()


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
