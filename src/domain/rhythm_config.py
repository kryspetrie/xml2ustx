"""Rhythm and groove settings for MusicXML conversion."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SwingPreset:
    """Named swing intensity preset."""

    preset_id: str
    intensity: int = 67


@dataclass(frozen=True)
class GroovePreset:
    """Named custom groove rules preset."""

    preset_id: str
    rules: str = ''


DEFAULT_SWING_PRESETS: tuple[SwingPreset, ...] = (
    SwingPreset('default', 67),
    SwingPreset('light', 40),
    SwingPreset('heavy', 85),
    SwingPreset('triplet', 100),
)

DEFAULT_GROOVE_PRESETS: tuple[GroovePreset, ...] = (
    GroovePreset('eighth-triplet', '8th: 2/3 1/3'),
    GroovePreset('sixteenth-shuffle', '16th: 0.6 0.4 0.4 0.6'),
)


@dataclass(frozen=True)
class RhythmConfig:
    """Swing and custom groove settings from application config."""

    rhythm_disabled: bool = False
    force_swing: bool = False
    force_groove: bool = False
    swing_intensity: int = 67
    groove: str = ''

    @classmethod
    def from_presets(
            cls,
            swing_presets: list[SwingPreset],
            groove_presets: list[GroovePreset],
            *,
            swing_preset_id: str = '',
            groove_preset_id: str = '',
            rhythm_disabled: bool = False,
            force_swing: bool = False,
            force_groove: bool = False) -> RhythmConfig:
        """Build runtime rhythm settings from preset libraries and selection."""
        swing_intensity = _resolve_swing_intensity(
            swing_presets,
            swing_preset_id,
            legacy_intensity=None,
        )
        groove = _resolve_groove_rules(
            groove_presets,
            groove_preset_id,
            legacy_groove='',
        )
        return cls(
            rhythm_disabled=rhythm_disabled,
            force_swing=force_swing,
            force_groove=force_groove,
            swing_intensity=swing_intensity,
            groove=groove,
        )

    @classmethod
    def from_mapping(cls, data: dict | None) -> RhythmConfig:
        """Build rhythm settings from a config YAML mapping."""
        if not data:
            return cls()

        rhythm_disabled = bool(data.get('rhythm_disabled', False))
        force_swing = bool(data.get('force_swing', data.get('swing_enabled', False)))
        force_groove = bool(data.get('force_groove', False))

        swing_presets = _parse_swing_presets(data)
        groove_presets = _parse_groove_presets(data)

        swing_preset_id = str(data.get('swing_preset', '') or '').strip()
        if not swing_preset_id and swing_presets:
            swing_preset_id = swing_presets[0].preset_id

        groove_preset_id = str(data.get('groove_preset', '') or '').strip()

        swing_intensity = _resolve_swing_intensity(
            swing_presets,
            swing_preset_id,
            legacy_intensity=data.get('swing_intensity'),
        )
        groove = _resolve_groove_rules(
            groove_presets,
            groove_preset_id,
            legacy_groove=data.get('groove'),
        )

        return cls(
            rhythm_disabled=rhythm_disabled,
            force_swing=force_swing,
            force_groove=force_groove,
            swing_intensity=swing_intensity,
            groove=groove,
        )

    def to_mapping(self) -> dict[str, object]:
        """Serialize to a config YAML-friendly mapping."""
        payload: dict[str, object] = {
            'rhythm_disabled': self.rhythm_disabled,
            'force_swing': self.force_swing,
            'force_groove': self.force_groove,
            'swing_intensity': self.swing_intensity,
        }
        if self.groove:
            payload['groove'] = self.groove
        return payload


def parse_swing_presets(data: dict) -> list[SwingPreset]:
    return _parse_swing_presets(data)


def parse_groove_presets(data: dict) -> list[GroovePreset]:
    return _parse_groove_presets(data)


def _parse_swing_presets(data: dict) -> list[SwingPreset]:
    raw_presets = data.get('swing_presets')
    if isinstance(raw_presets, list) and raw_presets:
        presets: list[SwingPreset] = []
        for item in raw_presets:
            if not isinstance(item, dict) or 'id' not in item:
                continue
            intensity_raw = item.get('intensity', 67)
            try:
                intensity = int(intensity_raw)
            except (TypeError, ValueError):
                intensity = 67
            presets.append(SwingPreset(
                preset_id=str(item['id']),
                intensity=max(0, min(100, intensity)),
            ))
        if presets:
            return presets

    legacy_intensity = data.get('swing_intensity', 67)
    try:
        intensity = int(legacy_intensity)
    except (TypeError, ValueError):
        intensity = 67
    return [SwingPreset('default', max(0, min(100, intensity)))]


def _parse_groove_presets(data: dict) -> list[GroovePreset]:
    raw_presets = data.get('groove_presets')
    if isinstance(raw_presets, list) and raw_presets:
        presets: list[GroovePreset] = []
        for item in raw_presets:
            if not isinstance(item, dict) or 'id' not in item:
                continue
            rules_raw = item.get('rules', '') or ''
            rules = rules_raw if isinstance(rules_raw, str) else str(rules_raw)
            presets.append(GroovePreset(
                preset_id=str(item['id']),
                rules=rules.strip(),
            ))
        if presets:
            return presets

    legacy_groove = data.get('groove', '') or ''
    if isinstance(legacy_groove, str) and legacy_groove.strip():
        return [GroovePreset('custom', legacy_groove.strip())]
    return list(DEFAULT_GROOVE_PRESETS)


def _resolve_swing_intensity(
        presets: list[SwingPreset],
        preset_id: str,
        *,
        legacy_intensity: object) -> int:
    if preset_id:
        for preset in presets:
            if preset.preset_id == preset_id:
                return preset.intensity

    if legacy_intensity is not None:
        try:
            return max(0, min(100, int(legacy_intensity)))
        except (TypeError, ValueError):
            pass

    if preset_id == '':
        return 67

    return presets[0].intensity if presets else 67


def _resolve_groove_rules(
        presets: list[GroovePreset],
        preset_id: str,
        *,
        legacy_groove: object) -> str:
    if preset_id:
        for preset in presets:
            if preset.preset_id == preset_id:
                return preset.rules

    legacy_text = legacy_groove if isinstance(legacy_groove, str) else ''
    return legacy_text.strip()
