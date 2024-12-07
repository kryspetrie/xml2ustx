from typing import List, Optional
from src.domain.models.TrackConfig import TrackConfig


class Job:

    def __init__(self, input_file: str, output_file: Optional[str], name: str,
                 track_configs: List[TrackConfig], default_lyric: str, debug: bool = False):
        self.input_file = input_file
        self.output_file = output_file
        self.name = name
        self.track_configs = track_configs
        self.default_lyric = default_lyric
        self.debug = debug



