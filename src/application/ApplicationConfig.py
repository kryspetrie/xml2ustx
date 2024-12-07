from typing import Dict, List

from src.domain.models.TrackConfig import TrackConfig
from src.domain.models.Voice import Voice


class ApplicationConfig:

    def __init__(self, voice_config_map: Dict[str, Voice],
                 track_config_map: Dict[str, List[TrackConfig]], default_lyric: str):
        self.voice_config_map = voice_config_map
        self.track_config_map = track_config_map
        self.default_lyric = default_lyric

    def default_voice_config(self):
        return self.voice_config_map['default']

    def default_track_config(self):
        return self.track_config_map['default']