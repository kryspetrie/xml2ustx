from typing import Dict, List

from src.models.TrackConfig import TrackConfig
from src.models.Voice import Voice


class ApplicationConfig:

    def __init__(self, voice_config_map: Dict[str, Voice], track_config_map: Dict[str, List[TrackConfig]]):
        self.voice_config_map = voice_config_map
        self.track_config_map = track_config_map
