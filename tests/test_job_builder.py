"""JobBuilder unit tests."""
from __future__ import annotations

from src.application.JobBuilder import build_cli, to_output_file
from src.application.models.CommandLineOptions import CommandLineOptions


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
