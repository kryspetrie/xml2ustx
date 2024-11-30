from typing import List

import TrackHelpers
from src.models.Tempo import Tempo
from src.models.TimeSignature import TimeSignature
from src.models.Track import Track


class Project:
    __slots__ = ('name', 'tick_resolution', 'tracks')

    def __init__(self, name: str, tick_resolution: int, tracks: List[Track]):
        self.name = name
        self.tick_resolution = tick_resolution
        self.tracks = tracks

    def find_unique_tempos(self) -> List[Tempo]:
        return TrackHelpers.find_unique_tempos(self.tracks)

    def find_unique_time_signatures(self) -> List[TimeSignature]:
        return TrackHelpers.find_unique_time_signatures(self.tracks)
