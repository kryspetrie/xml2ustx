"""Tests for config store helpers."""
from __future__ import annotations

import pytest

from src.ui.native.config_store import MAX_CONFIG_BYTES, read_config_text, validate_config_yaml


def test_validate_rejects_huge_yaml() -> None:
    huge = 'x' * (MAX_CONFIG_BYTES + 1)
    with pytest.raises(ValueError, match='too large'):
        validate_config_yaml(huge)


def test_read_rejects_huge_file(tmp_path) -> None:
    path = tmp_path / 'big.yml'
    path.write_bytes(b'#' + b'x' * (MAX_CONFIG_BYTES + 1))
    with pytest.raises(OSError, match='too large'):
        read_config_text(str(path))
