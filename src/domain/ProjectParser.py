from typing import List, cast
import math
import music21
import logging

from src.domain.models.TempoDown import TempoDown
from src.domain.models.TempoUp import TempoUp
from src.Utils import dumps
from src.domain.models.Event import Event
from src.domain.models.Tempo import Tempo
from src.domain.models.TimeSignature import TimeSignature
from src.domain.models.TrackConfig import TrackConfig
from src.domain.models.Note import Note
from src.domain.models.Track import Track
from src.domain.models.Project import Project


def __find_duration_by_offset(lines: list[music21.spanner.Line], offset: float) -> float | None:
    for line in lines:
        elements = line.spannerStorage.elements
        if elements is None or not elements:
            continue

        measures = [it for it in elements[0].containerHierarchy() if isinstance(it, music21.stream.Measure)]
        if not measures:
            logging.warning(f"Could not find measure associated with line {line}")
            return None

        measure_offset = measures[0].offset
        line_offset_in_measure = elements[0].offset
        line_offset = measure_offset + line_offset_in_measure

        if math.isclose(line_offset, offset, rel_tol=0, abs_tol=0.01):
            duration = line.spannerStorage.duration.quarterLength
            return duration
    return None


def __parse_text_expression(
        expression: music21.expressions.TextExpression,
        lines: list[music21.spanner.Line]) -> TempoDown | TempoUp | None:
    """
    Parse ritardando and accelerando markings from text expressions.
    NOTE: if there is no line associated with the expression, the marking is ignored.
    """
    def log_not_found():
        logging.warning(
            f"Could not find spanner line associated with {expression.content} " +
            f"at offset {expression.offset}. Ignoring expression.")

    # If this text expression is a ritardando
    if expression.content.startswith('rit'):
        duration = __find_duration_by_offset(lines, expression.offset)
        if duration is None:
            log_not_found()
            return None
        return TempoDown(expression.offset, duration)

    # If this text expression is an accelerando
    if expression.content.startswith('accel'):
        duration = __find_duration_by_offset(lines, expression.offset)
        if duration is None:
            log_not_found()
            return None
        return TempoUp(expression.offset, duration)

    return None


def parse(
        input_file: str,
        project_name: str,
        track_configs: list[TrackConfig],
        default_lyric: str,
        debug: bool = False):
    stream = music21.converter.parse(input_file)

    # This is a concept in MIDI and USTX, but not MusicXML
    tick_resolution = music21.defaults.ticksPerQuarter

    tracks: List[Track] = []

    # Unroll notated repeats
    stream = stream.expandRepeats()

    # Extend all tied notes into joined objects (e.g. ignore measure divisions)
    stream.stripTies(inPlace=True, matchByPitch=True)

    # TODO: rewrite durations and positions for swing

    # Unfortunately, Music21 does not provide us with a good mechanism to parse tempos changes.
    # We need to get these lines to inform us how to deal with "rit." and "accel." text elements.
    # We also need to get tempo markers at this point, since those are also stripped out.
    # These are stripped out of the stream by stream.voicesToParts() for some reason.
    flattened = stream.flatten()
    lines: list[music21.spanner.Line] = [it for it in flattened.parts.srcStreamElements if isinstance(it, music21.spanner.Line)]

    # Loop over the events first to get the tempo and time signature details
    project_events = []
    for event in flattened:
        # Add time signature events
        if isinstance(event, music21.meter.TimeSignature):
            time_signature_event: music21.meter.TimeSignature = cast(music21.meter.TimeSignature, event)
            time_signature: TimeSignature = TimeSignature(
                position=time_signature_event.offset,
                beat_per_bar=time_signature_event.numerator,
                beat_unit=time_signature_event.denominator)
            project_events.append(time_signature)
            continue

        if isinstance(event, music21.tempo.MetronomeMark):
            metronome_event: music21.tempo.MetronomeMark = cast(music21.tempo.MetronomeMark, event)
            tempo: Tempo = Tempo(position=metronome_event.offset, beats_per_minute=metronome_event.number)
            project_events.append(tempo)
            continue

        # Add ritardando events
        # NOTE: Music21 will never parse Musescore MusicXML 'rit.' into this object type!
        if isinstance(event, music21.tempo.RitardandoSpanner):
            rit_spanner: music21.tempo.RitardandoSpanner = cast(music21.tempo.RitardandoSpanner, event)
            tempo_down: TempoDown = TempoDown(rit_spanner.offset, rit_spanner.quarterLength)
            project_events.append(tempo_down)
            continue

        # Add accelerando events
        # NOTE: Music21 will never parse Musescore MusicXML 'accel.' into this object type!
        if isinstance(event, music21.tempo.AccelerandoSpanner):
            acc_spanner: music21.tempo.AccelerandoSpanner = cast(music21.tempo.AccelerandoSpanner, event)
            tempo_up: TempoUp = TempoUp(acc_spanner.offset, acc_spanner.quarterLength)
            project_events.append(tempo_up)
            continue

        # Parse text expressions for 'rit' and 'accel' tempo change indicators
        if isinstance(event, music21.expressions.TextExpression):
            expression: music21.expressions.TextExpression = cast(music21.expressions.TextExpression, event)
            parsed = __parse_text_expression(expression, lines)
            if parsed is not None:
                project_events.append(parsed)
            continue

    # Flatten all the different voices to distinct parts
    stream = stream.voicesToParts()

    # Loop over the parts and create Track list context
    for (index, part) in enumerate(stream.parts, 0):

        # Loop over supported events build Event list context
        track_events: List[Event] = []
        for event in part.flatten():

            # Add note events
            if isinstance(event, music21.note.Note) and event.isNote:
                note_event: music21.note.Note = cast(music21.note.Note, event)
                note: Note = Note(position=note_event.offset,
                                  duration=note_event.quarterLength,
                                  tone=note_event.pitch.midi,
                                  lyrics=note_event.lyric)
                track_events.append(note)
                continue

        # If we have a specific track config for this track, use it. Otherwise, default to first config.
        track_config: TrackConfig = track_configs[index] \
            if index < len(track_configs) \
            else track_configs[0]

        # Override the track name if specified in the config
        track_name = track_config.name \
            if (track_config.name is not None or track_config.name != "") \
            else part.partName

        track: Track = Track(
            name=track_name,
            voice=track_config.voice,
            pan=track_config.pan,
            volume=track_config.volume,
            events=track_events)
        tracks.append(track)

    project = Project(
        name=project_name,
        tick_resolution=tick_resolution,
        tracks=tracks,
        project_events=project_events,
        default_lyric=default_lyric)

    if debug:
        print(f'Parsed the following project:\n{dumps(project)}\n')

    return project