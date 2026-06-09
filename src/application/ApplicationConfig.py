"""Application configuration for XML to USTX conversion."""

from typing import Dict, List
from src.domain.models.TrackConfig import TrackConfig
from src.domain.models.Voice import Voice
from src.domain.rhythm_config import GroovePreset, RhythmConfig, SwingPreset


class ApplicationConfig:
    """Configuration class for application settings."""

    def __init__(
            self,
            voice_config_map: Dict[str, Voice],
            track_config_map: Dict[str, List[TrackConfig]],
            default_lyric: str,
            rhythm_config: RhythmConfig | None = None,
            swing_presets: list[SwingPreset] | None = None,
            groove_presets: list[GroovePreset] | None = None):
        self.voice_config_map = voice_config_map
        self.track_config_map = track_config_map
        self.default_lyric = default_lyric
        self.rhythm_config = rhythm_config or RhythmConfig()
        self.swing_presets = swing_presets or []
        self.groove_presets = groove_presets or []

    def default_voice_config(self):
        """Return the default voice configuration."""
        return self.voice_config_map['default']

    def default_track_config(self):
        """Return the default track configuration."""
        return self.track_config_map['default']