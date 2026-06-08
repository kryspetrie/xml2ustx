"""Xml2UstxRunner and session logging component tests."""
from __future__ import annotations

from pathlib import Path

import pytest

from src.application.conversion_errors import ConversionCancelledError
from src.application.models.CommandLineOptions import CommandLineOptions
from src.application.JobBuilder import build_cli
from src.application.session_log import SessionLogger
from src.application.Xml2UstxRunner import run_job
from src.domain.ProjectParser import parse as parse_project


def test_session_logger_writes_timestamped_lines(tmp_path: Path) -> None:
    messages: list[str] = []
    with SessionLogger(log_fn=messages.append, log_directory=tmp_path) as session:
        session.write('hello')
    assert session.path.exists()
    text = session.path.read_text(encoding='utf-8')
    assert 'hello' in text
    assert messages == ['hello']


def test_run_job_raises_when_cancelled_before_start(minimal_xml: Path, tmp_path: Path) -> None:
    output = tmp_path / 'out.ustx'
    options = CommandLineOptions(
        input_file=str(minimal_xml),
        output_file=str(output),
        input_dir=None,
        config_file=None,
        project_name='Cancel Test',
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
    with pytest.raises(ConversionCancelledError):
        run_job(job, should_cancel=lambda: True)


def test_run_job_writes_session_log(minimal_xml: Path, tmp_path: Path, monkeypatch) -> None:
    log_dir = tmp_path / 'logs'
    log_dir.mkdir()
    monkeypatch.setattr('src.application.session_log.default_log_directory', lambda: log_dir)
    output = tmp_path / 'out.ustx'
    options = CommandLineOptions(
        input_file=str(minimal_xml),
        output_file=str(output),
        input_dir=None,
        config_file=None,
        project_name='Log Test',
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
    outputs = run_job(job)
    assert outputs == [str(output)]
    assert list(log_dir.glob('*.log'))


def test_parse_raises_when_cancelled_before_musicxml(minimal_xml: Path, default_config: Path) -> None:
    from src.application.ConfigParser import parse as parse_config

    config = parse_config(str(default_config))
    track_configs = config.track_config_map['default']
    with pytest.raises(ConversionCancelledError):
        parse_project(
            str(minimal_xml),
            'Test',
            track_configs,
            config.default_lyric or 'doo',
            should_cancel=lambda: True,
        )
