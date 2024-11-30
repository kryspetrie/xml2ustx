from typing import List

from src.models.TimelineEvent import TimelineEvent
from src.models.Track import Track


class Project:
    __slots__ = ('name', 'tick_resolution', 'timeline_events', 'tracks')

    def __init__(self, name: str, tick_resolution: int,
                 timeline_events: List[TimelineEvent],
                 tracks: List[Track]):
        self.name = name
        self.tick_resolution = tick_resolution
        self.timeline_events = timeline_events
        self.tracks = tracks
