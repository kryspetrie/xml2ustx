from typing import List

from src.TrackHelpers import find_unique_tempos, find_unique_time_signatures
from src.models.Tempo import Tempo
from src.models.TimeSignature import TimeSignature
from src.models.Track import Track


class Project:

    def __init__(self, name: str, tick_resolution: int, tracks: List[Track], default_lyric: str):
        self.name = name
        self.tick_resolution = tick_resolution
        self.tracks = tracks
        self.default_lyric = default_lyric

    def find_unique_tempos(self) -> List[Tempo]:
        return find_unique_tempos(self.tracks)

    def find_unique_time_signatures(self) -> List[TimeSignature]:
        return find_unique_time_signatures(self.tracks)
