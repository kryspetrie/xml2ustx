from typing import List
from src.domain.models.TrackConfig import TrackConfig
from src.domain.rhythm_config import RhythmConfig


class Job:

    def __init__(
            self,
            input_files: list[str],
            output_files: list[str],
            name: str,
            track_configs: List[TrackConfig],
            default_lyric: str,
            rhythm_config: RhythmConfig | None = None,
            debug: bool = False):
        self.input_files = input_files
        self.output_files = output_files
        self.name = name
        self.track_configs = track_configs
        self.default_lyric = default_lyric
        self.rhythm_config = rhythm_config or RhythmConfig()
        self.debug = debug



