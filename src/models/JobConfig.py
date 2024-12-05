from typing import List
from src.models.TrackConfig import TrackConfig


class JobConfig:

    def __init__(self, input_file: str, output_file: str, name: str,
                 track_configs: List[TrackConfig], default_lyric: str):
        self.input_file = input_file
        self.output_file = output_file
        self.name = name
        self.track_configs = track_configs
        self.default_lyric = default_lyric



