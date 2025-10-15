from typing import List, Type, Set

from src.domain.models.Event import Event
from src.domain.models.Voice import Voice


class Track:

    def __init__(self, name: str, voice: Voice, pan: float, volume: float, events: List[Event]):
        self.name = name
        self.voice = voice
        self.pan = pan
        self.volume = volume
        self.events = events

    @staticmethod
    def __matches_any_type(event: Event, types: Set[Type]) -> bool:
        for event_type in types:
            if isinstance(event, event_type):
                return True
        return False

    def get_events_of_types(self, types: Set[Type]) -> List[Event]:
        return filter(lambda it: Track.__matches_any_type(it, types), self.events)

    def get_events_of_type(self, event_type: Type) -> List[Event]:
        return filter(lambda it: isinstance(it, event_type), self.events)



