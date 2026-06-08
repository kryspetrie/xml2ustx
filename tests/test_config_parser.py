"""ConfigParser component tests."""
from __future__ import annotations

from pathlib import Path

import pytest

from src.application.ConfigParser import parse as parse_config


def test_default_config_loads_voices_and_track_presets(default_config: Path) -> None:
    config = parse_config(str(default_config))
    assert 'default' in config.voice_config_map
    assert 'default' in config.track_config_map
    assert 'ttbb-barbershop' in config.track_config_map
    assert config.default_lyric == 'doo'


def test_track_config_references_known_voice(default_config: Path) -> None:
    config = parse_config(str(default_config))
    tracks = config.track_config_map['default']
    assert len(tracks) >= 1
    voice = tracks[0].voice
    assert voice.phonemizer is not None


def test_missing_voice_id_raises(tmp_path: Path) -> None:
    bad_config = tmp_path / 'bad.yml'
    bad_config.write_text(
        'voice_config:\n'
        '  - id: default\n'
        '    phonemizer: OpenUtau.Core.DefaultPhonemizer\n'
        'track_config:\n'
        '  - id: default\n'
        '    tracks:\n'
        '      - voice_id: missing\n',
        encoding='utf-8',
    )
    with pytest.raises(RuntimeError, match='Voice id missing'):
        parse_config(str(bad_config))


def test_invalid_yaml_raises(tmp_path: Path) -> None:
    bad_config = tmp_path / 'broken.yml'
    bad_config.write_text('voice_config: [', encoding='utf-8')
    with pytest.raises(RuntimeError, match='Invalid YAML'):
        parse_config(str(bad_config))
