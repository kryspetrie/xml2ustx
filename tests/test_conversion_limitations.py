"""Tests for lyric fallback during conversion."""
from __future__ import annotations

from pathlib import Path

from src.application.ConfigParser import parse as parse_config
from src.application.ConfigPaths import resolve_config_file
from src.domain.ProjectParser import parse as parse_project
from src.domain.lyric_helpers import DEFAULT_LYRIC, fill_missing_lyrics
from src.domain.models.Note import Note
from src.domain.models.Track import Track
from tests.fixtures.project_builders import default_voice


def test_fill_missing_lyrics_uses_default() -> None:
    track = Track(
        name='Lead',
        voice=default_voice(),
        pan=0.0,
        volume=0.0,
        events=[Note(position=0.0, duration=1.0, tone=60, lyrics='')],
    )

    fill_missing_lyrics([track], default_lyric='la')
    assert track.events[0].lyric == 'la'


def test_fill_missing_lyrics_falls_back_to_builtin_default() -> None:
    track = Track(
        name='Lead',
        voice=default_voice(),
        pan=0.0,
        volume=0.0,
        events=[Note(position=0.0, duration=1.0, tone=60, lyrics='')],
    )

    fill_missing_lyrics([track], default_lyric='')
    assert track.events[0].lyric == DEFAULT_LYRIC


def test_parse_minimal_musicxml_uses_score_lyrics(minimal_xml: Path) -> None:
    config = parse_config(resolve_config_file(None))
    track_configs = config.track_config_map['default']

    project = parse_project(
        str(minimal_xml),
        'Minimal',
        track_configs,
        config.default_lyric or 'doo',
    )

    assert project.tracks[0].events[0].lyric == 'la'


def test_parse_fills_missing_lyrics_from_default(minimal_xml: Path, tmp_path: Path) -> None:
    text = minimal_xml.read_text(encoding='utf-8')
    text = text.replace('<text>lo</text>', '<text></text>')
    broken = tmp_path / 'no-lyric.musicxml'
    broken.write_text(text, encoding='utf-8')

    config = parse_config(resolve_config_file(None))
    track_configs = config.track_config_map['default']

    project = parse_project(
        str(broken),
        'Broken',
        track_configs,
        'mm',
    )

    assert project.tracks[0].events[1].lyric == 'mm'
