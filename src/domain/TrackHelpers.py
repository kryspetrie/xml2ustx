from operator import attrgetter
from typing import List, Iterable, Set, Type, cast

from src.domain.models.Event import Event
from src.domain.models.TimeSignature import TimeSignature
from src.domain.models.Tempo import Tempo
from src.domain.models.TempoUp import TempoUp
from src.domain.models.TempoDown import TempoDown


def find_unique_time_signatures(events: List[Event]) -> List[TimeSignature]:
    return [cast(TimeSignature, x) for x in find_unique_events_for_type(events, TimeSignature)]


def find_unique_tempos_and_changes(events: List[Event]) -> List[Event]:
    tempos = [cast(Tempo, x) for x in find_unique_events_for_type(events, Tempo)]
    tempo_ups = [cast(TempoUp, x) for x in find_unique_events_for_type(events, TempoUp)]
    tempo_downs = [cast(TempoDown, x) for x in find_unique_events_for_type(events, TempoDown)]
    return __sort_events([*tempos, *tempo_ups, *tempo_downs])


def get_events_of_type(events: List[Event], event_type: Type) -> List[Event]:
    return filter(lambda it: isinstance(it, event_type), events)


def find_unique_events_for_type(events: List[Event], event_type: Type) -> List:
    elements: Set = set(get_events_of_type(events, event_type))
    return __sort_events(elements)


def __sort_events(events: Iterable[Event]) -> List[Event]:
    return sorted(events, key=attrgetter('position'))
