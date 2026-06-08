"""CLI argument parsing and end-to-end subprocess tests."""
from __future__ import annotations

import pytest

from src.application.CLIParser import parse as parse_cli
from src.application.version import get_version


def test_version_flag(cli_runner):
    result = cli_runner('--version')
    assert result.returncode == 0
    assert get_version() in result.stdout


def test_list_track_configs(cli_runner, default_config):
    result = cli_runner('--list_track_configs', '--config_file', str(default_config))
    assert result.returncode == 0
    ids = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    assert 'default' in ids
    assert 'ttbb-barbershop' in ids


def test_cli_requires_input(monkeypatch):
    monkeypatch.setattr('sys.argv', ['main.py'])
    with pytest.raises(SystemExit) as exc:
        parse_cli()
    assert exc.value.code == 1


def test_cli_rejects_both_input_sources(monkeypatch):
    monkeypatch.setattr(
        'sys.argv',
        ['main.py', '--input_file', 'a.xml', '--input_dir', '/tmp'],
    )
    with pytest.raises(SystemExit) as exc:
        parse_cli()
    assert exc.value.code == 1


def test_cli_appends_ustx_extension(monkeypatch):
    monkeypatch.setattr(
        'sys.argv',
        ['main.py', '--input_file', 'tests/fixtures/minimal.musicxml', '--output_file', '/tmp/outfile'],
    )
    options = parse_cli()
    assert options.output_file == '/tmp/outfile.ustx'


def test_convert_minimal_musicxml(cli_runner, minimal_xml, tmp_path):
    output = tmp_path / 'minimal.ustx'
    result = cli_runner(
        '--input_file',
        str(minimal_xml),
        '--track_config',
        'default',
        '--project_name',
        'Minimal Test',
        '--output_file',
        str(output),
    )
    assert result.returncode == 0, result.stderr
    assert output.exists()
    text = output.read_text(encoding='utf-8')
    assert 'name: Minimal Test' in text
    assert 'lyric: "la"' in text or 'lyric: la' in text
    assert 'lyric: "lo"' in text or 'lyric: lo' in text


def test_convert_input_file_without_input_dir(cli_runner, minimal_xml, tmp_path):
    """Regression: --input_file alone must not call get_input_files_from_dir(None)."""
    output = tmp_path / 'single.ustx'
    result = cli_runner(
        '--input_file',
        str(minimal_xml),
        '--output_file',
        str(output),
    )
    assert result.returncode == 0, result.stderr
    assert output.exists()
