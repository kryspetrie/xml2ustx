"""Tests for structured config editor data helpers."""
from __future__ import annotations

from src.ui.native.config_data import parse_config_document, serialize_config_document
from src.ui.native.config_store import shipped_config_text, validate_config_yaml


def test_config_document_round_trip_matches_shipped_default() -> None:
    text = shipped_config_text()
    document = parse_config_document(text)
    round_trip = serialize_config_document(document)

    validate_config_yaml(round_trip)
    assert 'voice_config:' in round_trip
    assert 'track_config:' in round_trip
    assert document.default_lyric == 'doo'
    assert any(voice.voice_id == 'default' for voice in document.voices)
    assert any(preset.preset_id == 'default' for preset in document.track_presets)
