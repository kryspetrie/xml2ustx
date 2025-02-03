from typing import cast, List
from enum import (Enum)

import jsonpickle
import logging

from src.domain.models.Tempo import Tempo
from src.domain.models.Event import Event
from src.domain.models.TempoDown import TempoDown

from src.domain.models.TempoUp import TempoUp


class TempoChange:
    class ChangeType(Enum):
        TEMPO = 1
        TEMPO_UP = 2
        TEMPO_DOWN = 3

    def __init__(self,
                 position: float,
                 change_type: ChangeType,
                 duration: float | None = None,
                 beats_per_minute_start: float | None = None,
                 beats_per_minute_end: float | None = None):
        self.position = position
        self.duration = duration
        self.beats_per_minute_start = beats_per_minute_start
        self.beats_per_minute_end = beats_per_minute_end
        self.change_type = change_type

    def __repr__(self):
        return jsonpickle.dumps(self, unpicklable=False)

    @staticmethod
    def default():
        TempoChange(
            position=0,
            change_type=TempoChange.ChangeType.TEMPO,
            beats_per_minute_start=120,
            beats_per_minute_end=120)

    @staticmethod
    def from_event(tempo_event: Event):
        if isinstance(tempo_event, Tempo):
            as_tempo = cast(Tempo, tempo_event)
            return TempoChange(
                position=as_tempo.position,
                beats_per_minute_start=as_tempo.beats_per_minute,
                beats_per_minute_end=as_tempo.beats_per_minute,
                change_type=TempoChange.ChangeType.TEMPO)
        if isinstance(tempo_event, TempoUp):
            as_tempo_up = cast(TempoUp, tempo_event)
            return TempoChange(
                position=as_tempo_up.position,
                duration=as_tempo_up.duration,
                change_type=TempoChange.ChangeType.TEMPO_UP)
        if isinstance(tempo_event, TempoDown):
            as_tempo_down = cast(TempoDown, tempo_event)
            return TempoChange(
                position=as_tempo_down.position,
                duration=as_tempo_down.duration,
                change_type=TempoChange.ChangeType.TEMPO_DOWN)
        raise TypeError(f"Expected event of types [Tempo, TempoUp, TempoDown]. Got {type(tempo_event)}")

    def resolve_tempos(self, tempo_change_interval: float) -> List[Tempo]:
        if self.beats_per_minute_start is None or self.beats_per_minute_end is None:
            raise RuntimeError("TempoChanges have not been processed. Tempo start and end must not be None.")

        start_bpm = self.beats_per_minute_start
        end_bpm = self.beats_per_minute_end

        # Base case - tempo with no changes
        if self.duration is None or self.duration == 0 or start_bpm == end_bpm:
            return [Tempo(position=self.position, beats_per_minute=start_bpm)]

        # Tempo change over time
        num_changes = max(int(self.duration / tempo_change_interval), 1)
        bpm_interval = (end_bpm - start_bpm) / num_changes
        pos_interval = self.duration / num_changes
        cur_bpm = float(start_bpm)
        cur_pos = self.position
        resolved: List[Tempo] = []
        for _ in range(num_changes):
            resolved.append(Tempo(position=cur_pos, beats_per_minute=cur_bpm))
            cur_pos += pos_interval
            cur_bpm += bpm_interval
        end_pos = self.position + self.duration
        resolved.append(Tempo(position=end_pos, beats_per_minute=end_bpm))
        return resolved


def __resolve_all_tempos(changes: list[TempoChange], tempo_change_interval: float) -> list[Tempo]:
    for change in changes:
        # Note: this will probably come up a lot, since there are no tests, lol
        if change.beats_per_minute_start is None or change.beats_per_minute_end is None:
            msg = f"Could not resolve all tempo changes! {changes}"
            logging.error(msg)
            raise RuntimeError("Could not resolve all tempo changes")

    list_of_lists: list[list[Tempo]] = [
        change.resolve_tempos(tempo_change_interval)
        for change in changes]

    merged: list[Tempo] = [item for sublist in list_of_lists for item in sublist]
    return merged


def __set_start_and_end_bpms_in_place(changes: list[TempoChange], tempo_change_amount: float):
    while True:
        updates = 0
        updates += __set_blank_bpms_by_adjacent(changes)
        updates += __set_blank_end_bpm_for_changes(changes, tempo_change_amount)
        updates += __set_blank_bpms_by_adjacent(changes)
        updates += __set_blank_start_bpm_for_changes(changes, tempo_change_amount)
        if updates == 0:
            break


def __keep_unique_by_position(tempos: list[Tempo]) -> list[Tempo]:
    seen = set()
    unique_tempos = [x for x in tempos if x not in seen and not seen.add(x)]
    return unique_tempos


def __keep_only_first_tempo_change_with_same_value(tempos: list[Tempo]) -> list[Tempo]:
    kept = []
    previous = None
    for current in tempos:
        # Base case
        if previous is None:
            kept.append(current)
            previous = current
            continue

        if previous.beats_per_minute == current.beats_per_minute:
            continue

        previous = current
        kept.append(current)

    return kept


def interpolate_tempos(
        events: list[Event],
        tempo_change_amount: float = 0.2,
        tempo_change_interval: float = 0.25) -> List[Tempo]:
    # Convert to our internal format for interpolation
    changes = __to_tempo_changes(events)

    # Fill in our start bpm and end bpm for all tempo changes
    __set_start_and_end_bpms_in_place(changes, tempo_change_amount)

    # Interpolate tempos within the tempo change ranges
    tempos = __resolve_all_tempos(changes, tempo_change_interval)

    # Keep only one tempo per positional offset in the project
    tempos = __keep_unique_by_position(tempos)

    # Keep only the first of all consecutive equal tempo values
    tempos = __keep_only_first_tempo_change_with_same_value(tempos)

    return tempos


def __to_tempo_changes(events: list[Event]) -> list[TempoChange]:
    changes: List[TempoChange] = []

    # If there are NO fixed tempos at all, default to 120bpm
    if not any(isinstance(item, Tempo) for item in events):
        changes += TempoChange.default()

    changes += [TempoChange.from_event(it) for it in events]
    return changes


def __set_blank_bpms_by_adjacent(changes: List[TempoChange]):
    """
    Scan over the list and set blank BPMs per adjacent resolved tempos
    If two gradual tempo changes are next to each other, then some BPMs will still be blank
    """
    updates = 0
    for idx in range(0, len(changes)):
        cur_change = changes[idx]
        if cur_change.beats_per_minute_start is None:
            cur_change.beats_per_minute_start = __prev_adjacent_bpm(changes, idx)
            updates += 1
        if cur_change.beats_per_minute_end is None:
            cur_change.beats_per_minute_end = __next_adjacent_bpm(changes, idx)
            updates += 1
    return updates


def __set_blank_end_bpm_for_changes(changes: List[TempoChange], tempo_change_amount: float) -> int:
    """
    Scan over the list and fill in the blank end bpm based on a tempo-change amount
    Only look at the expected cases where we know the left side of the expression
    """
    updates = 0
    for change in changes:
        start_bpm = change.beats_per_minute_start
        end_bpm = change.beats_per_minute_end
        if change.change_type is TempoChange.ChangeType.TEMPO_UP:
            if start_bpm is not None and end_bpm is None:
                end_tempo = cast(float, start_bpm) * (1 + tempo_change_amount)
                change.beats_per_minute_end = end_tempo
                updates += 1
                continue
        if change.change_type is TempoChange.ChangeType.TEMPO_DOWN:
            if start_bpm is not None and end_bpm is None:
                end_tempo = cast(float, start_bpm) * (1 - tempo_change_amount)
                change.beats_per_minute_end = end_tempo
                updates += 1
    return updates


def __set_blank_start_bpm_for_changes(changes: List[TempoChange], tempo_change_amount: float) -> int:
    """
    Scan over the list and fill in the blank start bpm based on a tempo-change amount
    Only look at the expected cases where we know the right side of the expression
    """
    updates = 0
    for change in changes:
        start_bpm = change.beats_per_minute_start
        end_bpm = change.beats_per_minute_end
        if change.change_type is TempoChange.ChangeType.TEMPO_UP:
            if start_bpm is None and end_bpm is not None:
                start_tempo = cast(float, end_bpm) * (1 - tempo_change_amount)
                change.beats_per_minute_start = start_tempo
                updates += 1
                continue
        if change.change_type is TempoChange.ChangeType.TEMPO_DOWN:
            if start_bpm is None and end_bpm is not None:
                start_tempo = cast(float, end_bpm) * (1 + tempo_change_amount)
                change.beats_per_minute_start = start_tempo
                updates += 1
    return updates


def __next_adjacent_bpm(changes: List[TempoChange], cur_idx: int) -> float | None:
    next_idx = cur_idx + 1
    if next_idx >= len(changes):
        return None
    next_change: TempoChange = changes[next_idx]
    return next_change.beats_per_minute_start


def __prev_adjacent_bpm(changes: List[TempoChange], cur_idx: int) -> float | None:
    prev_idx = cur_idx - 1
    if prev_idx < 0:
        return None
    prev_change: TempoChange = changes[prev_idx]
    return prev_change.beats_per_minute_end
