from typing import List

from src.models.TrackEvent import TrackEvent
from src.models.Voice import Voice


class Track:
    __slots__ = ('name', 'voice', 'pan', 'volume', 'events')

    def __init__(self, name: str, voice: Voice, pan: float, volume: float, events: List[TrackEvent]):
        self.name = name
        self.voice = voice
        self.pan = pan
        self.volume = volume
        self.events = events
