"""Application configuration for XML to USTX conversion."""

from typing import Dict, List
from src.domain.models.TrackConfig import TrackConfig
from src.domain.models.Voice import Voice


class ApplicationConfig:
    """Configuration class for application settings."""

    def __init__(self, voice_config_map: Dict[str, Voice],
                 track_config_map: Dict[str, List[TrackConfig]], default_lyric: str):
        self.voice_config_map = voice_config_map
        self.track_config_map = track_config_map
        self.default_lyric = default_lyric

    def default_voice_config(self):
        """Return the default voice configuration."""
        return self.voice_config_map['default']

    def default_track_config(self):
        """Return the default track configuration."""
        return self.track_config_map['default']