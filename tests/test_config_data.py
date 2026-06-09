"""Tests for structured config editor data helpers."""
from __future__ import annotations

from src.ui.native.config_data import (
    ConfigDocument,
    GroovePresetRow,
    SwingPresetRow,
    parse_config_document,
    serialize_config_document,
)
from src.ui.native.config_store import shipped_config_text, validate_config_yaml


def test_config_document_round_trip_matches_shipped_default() -> None:
    text = shipped_config_text()
    document = parse_config_document(text)
    round_trip = serialize_config_document(document)

    validate_config_yaml(round_trip)
    assert 'voice_config:' in round_trip
    assert 'track_config:' in round_trip
    assert 'swing_presets:' in round_trip
    assert 'groove_presets:' in round_trip
    assert 'swing_preset:' not in round_trip
    assert 'rhythm_disabled:' not in round_trip
    assert document.default_lyric == 'doo'
    assert any(preset.preset_id == 'default' for preset in document.swing_presets)
    assert any(preset.preset_id == 'eighth-triplet' for preset in document.groove_presets)
    assert any(voice.voice_id == 'default' for voice in document.voices)
    assert any(preset.preset_id == 'default' for preset in document.track_presets)


def test_config_document_round_trip_preset_definitions() -> None:
    document = ConfigDocument(
        default_lyric='la',
        swing_presets=[
            SwingPresetRow('default', 67),
            SwingPresetRow('heavy', 85),
        ],
        groove_presets=[
            GroovePresetRow('eighth-triplet', '8th: 2/3 1/3'),
        ],
    )
    parsed = parse_config_document(serialize_config_document(document))
    assert parsed.swing_presets[1].intensity == 85
    assert parsed.groove_presets[0].rules == '8th: 2/3 1/3'
