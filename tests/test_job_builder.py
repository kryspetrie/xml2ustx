"""JobBuilder unit tests."""
from __future__ import annotations

from src.application.JobBuilder import build_cli, build_native, to_output_file
from src.application.models.CommandLineOptions import CommandLineOptions
from src.application.models.NativeUiOptions import NativeUiOptions


def test_to_output_file_replaces_extension():
    assert to_output_file('/tmp/song.musicxml') == '/tmp/song.ustx'


def test_build_cli_single_input_file():
    options = CommandLineOptions(
        input_file='tests/fixtures/minimal.musicxml',
        output_file='out.ustx',
        input_dir=None,
        config_file=None,
        project_name='Test Project',
        track_config_id='default',
        voice_config_ids=None,
        volumes=None,
        pans=None,
        tracks=None,
        debug=False,
        open_in_openutau=False,
        openutau_path=None,
    )
    job = build_cli(options)
    assert job.input_files == ['tests/fixtures/minimal.musicxml']
    assert job.output_files == ['out.ustx']
    assert job.name == 'Test Project'
    assert len(job.track_configs) == 1


def test_build_native_uses_convert_tab_rhythm_selection() -> None:
    options = NativeUiOptions(
        input_files=['tests/fixtures/minimal.musicxml'],
        track_config_id='default',
        swing_preset_id='heavy',
        groove_preset_id='eighth-triplet',
        force_swing=True,
    )
    job = build_native(options)
    assert job.rhythm_config.swing_intensity == 85
    assert job.rhythm_config.groove.startswith('8th:')
    assert job.rhythm_config.force_swing is True
