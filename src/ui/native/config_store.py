"""Config file load/save/validate helpers."""
from __future__ import annotations

import tempfile
from pathlib import Path

import yaml

from src.application.ConfigParser import parse as parse_config
from src.application.ConfigPaths import resolve_config_file
from src.resources.Resources import get_resource_path

MAX_CONFIG_BYTES = 2 * 1024 * 1024


def default_config_path() -> str:
    return str(resolve_config_file(None))


def shipped_config_text() -> str:
    return get_resource_path('config.yml').read_text(encoding='utf-8')


def read_config_text(path: str) -> str:
    config_path = Path(path)
    size = config_path.stat().st_size
    if size > MAX_CONFIG_BYTES:
        raise OSError(
            f'Config file is too large ({size} bytes). '
            f'Maximum supported size is {MAX_CONFIG_BYTES} bytes.')
    return config_path.read_text(encoding='utf-8')


def write_config_text(path: str, text: str) -> None:
    encoded = text.encode('utf-8')
    if len(encoded) > MAX_CONFIG_BYTES:
        raise ValueError(
            f'Config text is too large ({len(encoded)} bytes). '
            f'Maximum supported size is {MAX_CONFIG_BYTES} bytes.')
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(text, encoding='utf-8')


def validate_config_yaml(text: str) -> None:
    if len(text.encode('utf-8')) > MAX_CONFIG_BYTES:
        raise ValueError(
            f'Config text is too large. Maximum supported size is {MAX_CONFIG_BYTES} bytes.')
    data = yaml.safe_load(text)
    if not isinstance(data, dict):
        raise ValueError('Config root must be a YAML mapping.')
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False, encoding='utf-8') as tmp:
        tmp.write(text)
        tmp_path = tmp.name
    try:
        parse_config(tmp_path)
    finally:
        Path(tmp_path).unlink(missing_ok=True)
