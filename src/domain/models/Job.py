from typing import List, Optional
from src.domain.models.TrackConfig import TrackConfig


class Job:

    def __init__(self, input_files: list[str], output_files: list[str], name: str,
                 track_configs: List[TrackConfig], default_lyric: str, debug: bool = False):
        self.input_files = input_files
        self.output_files = output_files
        self.name = name
        self.track_configs = track_configs
        self.default_lyric = default_lyric
        self.debug = debug



