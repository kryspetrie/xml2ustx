"""Tests for rhythm preset resolution from config."""
from __future__ import annotations

from src.domain.rhythm_config import RhythmConfig, SwingPreset, GroovePreset


def test_from_mapping_resolves_selected_presets() -> None:
    config = RhythmConfig.from_mapping({
        'swing_preset': 'heavy',
        'swing_presets': [
            {'id': 'default', 'intensity': 67},
            {'id': 'heavy', 'intensity': 85},
        ],
        'groove_preset': 'shuffle',
        'groove_presets': [
            {'id': 'shuffle', 'rules': '16th: 0.6 0.4 0.4 0.6'},
        ],
        'force_groove': True,
    })
    assert config.swing_intensity == 85
    assert config.groove == '16th: 0.6 0.4 0.4 0.6'
    assert config.force_groove is True


def test_from_mapping_legacy_swing_intensity_and_groove() -> None:
    config = RhythmConfig.from_mapping({
        'swing_intensity': 55,
        'groove': '8th: 2/3 1/3',
    })
    assert config.swing_intensity == 55
    assert config.groove == '8th: 2/3 1/3'


def test_from_mapping_empty_groove_preset_yields_no_groove() -> None:
    config = RhythmConfig.from_mapping({
        'groove_preset': '',
        'groove_presets': [
            {'id': 'shuffle', 'rules': '16th: 0.6 0.4 0.4 0.6'},
        ],
    })
    assert config.groove == ''


def test_from_presets_uses_selected_preset_ids() -> None:
    config = RhythmConfig.from_presets(
        [SwingPreset('default', 67), SwingPreset('heavy', 85)],
        [GroovePreset('shuffle', '16th: 0.6 0.4 0.4 0.6')],
        swing_preset_id='heavy',
        groove_preset_id='shuffle',
        force_swing=True,
    )
    assert config.swing_intensity == 85
    assert config.groove.startswith('16th:')
    assert config.force_swing is True
