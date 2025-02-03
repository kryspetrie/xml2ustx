from operator import attrgetter
from typing import List, Iterable, Set, Type, cast

from src.domain.models.Event import Event
from src.domain.models.Track import Track
from src.domain.models.TimeSignature import TimeSignature
from src.domain.models.Tempo import Tempo
from src.domain.models.TempoUp import TempoUp
from src.domain.models.TempoDown import TempoDown


def find_unique_time_signatures(tracks: List[Track]) -> List[TimeSignature]:
    return [cast(TimeSignature, x) for x in find_unique_events_for_type(tracks, TimeSignature)]


def find_unique_tempos_and_changes(tracks: List[Track]) -> List[Event]:
    tempos = [cast(Tempo, x) for x in find_unique_events_for_type(tracks, Tempo)]
    tempo_ups = [cast(TempoUp, x) for x in find_unique_events_for_type(tracks, TempoUp)]
    tempo_downs = [cast(TempoDown, x) for x in find_unique_events_for_type(tracks, TempoDown)]
    return __sort_events([*tempos, *tempo_ups, *tempo_downs])


def find_unique_events_for_type(tracks: List[Track], event_type: Type) -> List:
    elements: Set = set()
    for track in tracks:
        elements.update(track.get_events_of_type(event_type))
    return __sort_events(elements)


def __sort_events(events: Iterable[Event]) -> List[Event]:
    return sorted(events, key=attrgetter('position'))
