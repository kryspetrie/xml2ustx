"""Structured config document models for the native config editor."""
from __future__ import annotations

from dataclasses import dataclass, field

import yaml

from src.domain.rhythm_config import (
    DEFAULT_GROOVE_PRESETS,
    DEFAULT_SWING_PRESETS,
    parse_groove_presets,
    parse_swing_presets,
)


@dataclass
class VoiceConfigRow:
    """One voice preset entry from ``voice_config``."""

    voice_id: str
    singer: str = ''
    renderer: str = ''
    phonemizer: str = ''


@dataclass
class TrackConfigRow:
    """One track mapping inside a track preset."""

    voice_id: str
    track_name: str = ''
    pan: float = 0.0
    volume: float = 0.0


@dataclass
class TrackPresetRow:
    """One named track preset from ``track_config``."""

    preset_id: str
    tracks: list[TrackConfigRow] = field(default_factory=list)


@dataclass
class SwingPresetRow:
    """One named swing intensity preset."""

    preset_id: str
    intensity: int = 67


@dataclass
class GroovePresetRow:
    """One named custom groove preset."""

    preset_id: str
    rules: str = ''


@dataclass
class ConfigDocument:
    """Editable representation of ``config.yml``."""

    voices: list[VoiceConfigRow] = field(default_factory=list)
    track_presets: list[TrackPresetRow] = field(default_factory=list)
    default_lyric: str = 'doo'
    swing_presets: list[SwingPresetRow] = field(default_factory=list)
    groove_presets: list[GroovePresetRow] = field(default_factory=list)


def _default_swing_preset_rows() -> list[SwingPresetRow]:
    return [
        SwingPresetRow(preset.preset_id, preset.intensity)
        for preset in DEFAULT_SWING_PRESETS
    ]


def _default_groove_preset_rows() -> list[GroovePresetRow]:
    return [
        GroovePresetRow(preset.preset_id, preset.rules)
        for preset in DEFAULT_GROOVE_PRESETS
    ]


def parse_config_document(text: str) -> ConfigDocument:
    """Parse YAML config text into a structured document."""
    data = yaml.safe_load(text)
    if not isinstance(data, dict):
        raise ValueError('Config root must be a YAML mapping.')

    voices: list[VoiceConfigRow] = []
    for item in data.get('voice_config', []):
        if not isinstance(item, dict) or 'id' not in item:
            raise ValueError('Each voice config entry must be a mapping with an id.')
        voices.append(VoiceConfigRow(
            voice_id=str(item['id']),
            singer=str(item.get('singer', '') or ''),
            renderer=str(item.get('renderer', '') or ''),
            phonemizer=str(item.get('phonemizer', '') or ''),
        ))

    track_presets: list[TrackPresetRow] = []
    for preset in data.get('track_config', []):
        if not isinstance(preset, dict) or 'id' not in preset:
            raise ValueError('Each track config entry must be a mapping with an id.')
        tracks: list[TrackConfigRow] = []
        for track in preset.get('tracks', []):
            if not isinstance(track, dict) or 'voice_id' not in track:
                raise ValueError('Each track entry must include voice_id.')
            tracks.append(TrackConfigRow(
                voice_id=str(track['voice_id']),
                track_name=str(track.get('track_name', '') or ''),
                pan=float(track.get('pan', 0.0)),
                volume=float(track.get('volume', 0.0)),
            ))
        track_presets.append(TrackPresetRow(
            preset_id=str(preset['id']),
            tracks=tracks,
        ))

    default_lyric = str(data.get('default_lyric', 'doo') or 'doo')
    swing_presets = [
        SwingPresetRow(preset.preset_id, preset.intensity)
        for preset in parse_swing_presets(data)
    ]
    groove_presets = [
        GroovePresetRow(preset.preset_id, preset.rules)
        for preset in parse_groove_presets(data)
    ]

    return ConfigDocument(
        voices=voices,
        track_presets=track_presets,
        default_lyric=default_lyric,
        swing_presets=swing_presets or _default_swing_preset_rows(),
        groove_presets=groove_presets or _default_groove_preset_rows(),
    )


def serialize_config_document(document: ConfigDocument) -> str:
    """Serialize a structured config document to YAML text."""
    voice_config: list[dict[str, str]] = []
    for voice in document.voices:
        item: dict[str, str] = {'id': voice.voice_id}
        if voice.singer:
            item['singer'] = voice.singer
        if voice.renderer:
            item['renderer'] = voice.renderer
        if voice.phonemizer:
            item['phonemizer'] = voice.phonemizer
        voice_config.append(item)

    track_config: list[dict] = []
    for preset in document.track_presets:
        tracks: list[dict] = []
        for track in preset.tracks:
            item: dict = {'voice_id': track.voice_id}
            if track.track_name:
                item['track_name'] = track.track_name
            if track.pan != 0.0:
                item['pan'] = track.pan
            if track.volume != 0.0:
                item['volume'] = track.volume
            tracks.append(item)
        track_config.append({'id': preset.preset_id, 'tracks': tracks})

    swing_presets: list[dict[str, object]] = []
    for preset in document.swing_presets:
        swing_presets.append({'id': preset.preset_id, 'intensity': preset.intensity})

    groove_presets: list[dict[str, str]] = []
    for preset in document.groove_presets:
        item: dict[str, str] = {'id': preset.preset_id}
        if preset.rules.strip():
            item['rules'] = preset.rules.rstrip() + '\n'
        else:
            item['rules'] = ''
        groove_presets.append(item)

    payload = {
        'voice_config': voice_config,
        'track_config': track_config,
        'default_lyric': document.default_lyric,
        'swing_presets': swing_presets,
        'groove_presets': groove_presets,
    }
    return yaml.dump(payload, sort_keys=False, allow_unicode=True, default_flow_style=False)
