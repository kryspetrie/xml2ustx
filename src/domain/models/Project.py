from typing import List

from src.domain.models.Event import Event
from src.domain.models.Tempo import Tempo
from src.domain.TrackHelpers import find_unique_tempos_and_changes, find_unique_time_signatures
from src.domain.models.TimeSignature import TimeSignature
from src.domain.models.Track import Track


class Project:

    def __init__(self, name: str, tick_resolution: int, tracks: List[Track], default_lyric: str):
        self.name = name
        self.tick_resolution = tick_resolution
        self.tracks = tracks
        self.default_lyric = default_lyric

    def find_unique_time_signatures(self) -> List[TimeSignature]:
        return find_unique_time_signatures(self.tracks)


    def find_unique_tempos_and_changes(self) -> List[Event]:
        return find_unique_tempos_and_changes(self.tracks)
