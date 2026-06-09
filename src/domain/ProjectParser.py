from __future__ import annotations

from typing import List, cast
import math
import music21
import logging

from src.domain.models.TempoDown import TempoDown
from src.domain.models.TempoUp import TempoUp
from src.Utils import dumps
from collections.abc import Callable

from src.application.conversion_errors import ConversionCancelledError
from src.application.conversion_limitations import warn_unsupported_score_features
from src.application.conversion_log import LogFn, emit_log
from src.domain.dynamics_parser import nearest_vol_at_position, parse_dynamics
from src.domain.lyric_helpers import (
    extract_note_lyric,
    fill_missing_lyrics,
    merge_syllabic_lyrics_in_part,
    merge_tied_lyrics_in_place,
)
from src.domain.groove_parser import apply_groove_rules
from src.domain.score_rhythm_detection import (
    parse_swing_intensity_from_score,
    resolve_rhythm_rules,
    score_has_groove_annotation,
    score_has_swing_annotation,
)
from src.domain.rhythm_config import RhythmConfig
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


def __raise_if_cancelled(should_cancel: Callable[[], bool] | None) -> None:
    if should_cancel and should_cancel():
        raise ConversionCancelledError('Conversion cancelled during parse.')


def parse(
        input_file: str,
        project_name: str,
        track_configs: list[TrackConfig],
        default_lyric: str,
        rhythm_config: RhythmConfig | None = None,
        debug: bool = False,
        log_fn: LogFn | None = None,
        should_cancel: Callable[[], bool] | None = None):
    rhythm = rhythm_config or RhythmConfig()
    __raise_if_cancelled(should_cancel)
    stream = music21.converter.parse(input_file)

    # This is a concept in MIDI and USTX, but not MusicXML
    tick_resolution = music21.defaults.ticksPerQuarter

    tracks: List[Track] = []

    # Unroll notated repeats
    stream = stream.expandRepeats()

    # Unfortunately, Music21 does not provide us with a good mechanism to parse tempos changes.
    # We need to get these lines to inform us how to deal with "rit." and "accel." text elements.
    # We also need to get tempo markers at this point, since those are also stripped out.
    # These are stripped out of the stream by stream.voicesToParts() for some reason.
    flattened = stream.flatten()
    lines: list[music21.spanner.Line] = [it for it in flattened.parts.srcStreamElements if isinstance(it, music21.spanner.Line)]

    warn_unsupported_score_features(flattened, log_fn=log_fn)

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
            tempo: Tempo = Tempo(
                position=metronome_event.offset,
                beats_per_minute=_quarter_note_bpm(metronome_event),
            )
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

    dynamics_breakpoints = parse_dynamics(flattened)
    has_swing = score_has_swing_annotation(stream, flattened)
    has_groove = score_has_groove_annotation(stream, flattened)
    score_swing_intensity = parse_swing_intensity_from_score(stream, flattened)
    rhythm_rules = resolve_rhythm_rules(
        rhythm,
        has_swing_annotation=has_swing,
        has_groove_annotation=has_groove,
        score_swing_intensity=score_swing_intensity,
    )

    # Flatten all the different voices to distinct parts
    stream = stream.voicesToParts()

    if rhythm_rules:
        if rhythm.groove.strip() and has_groove:
            emit_log('Applying groove from score marking.', log_fn=log_fn)
        elif rhythm.groove.strip() and rhythm.force_groove:
            emit_log('Applying forced groove.', log_fn=log_fn)
        elif has_swing:
            emit_log(
                f'Applying swing from score marking ({score_swing_intensity or rhythm.swing_intensity}% intensity).',
                log_fn=log_fn,
            )
        elif rhythm.force_swing:
            emit_log(
                f'Applying forced swing ({rhythm.swing_intensity}% intensity).',
                log_fn=log_fn,
            )
        for part in stream.parts:
            apply_groove_rules(part, rhythm_rules)

    merge_tied_lyrics_in_place(stream)
    for part in stream.parts:
        merge_syllabic_lyrics_in_part(part)

    # Extend all tied notes into joined objects (e.g. ignore measure divisions)
    stream.stripTies(matchByPitch=True, inPlace=True)

    # Loop over the parts and create Track list context
    for (index, part) in enumerate(stream.parts, 0):
        __raise_if_cancelled(should_cancel)

        # Loop over supported events build Event list context
        track_events: List[Event] = []
        for event in part.flatten():

            # Add note events
            if isinstance(event, music21.note.Note) and event.isNote:
                note_event: music21.note.Note = cast(music21.note.Note, event)
                note: Note = Note(
                    position=note_event.offset,
                    duration=note_event.quarterLength,
                    tone=note_event.pitch.midi,
                    lyrics=extract_note_lyric(note_event),
                    volume=nearest_vol_at_position(dynamics_breakpoints, note_event.offset),
                )
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

    fill_missing_lyrics(tracks, default_lyric)

    project = Project(
        name=project_name,
        tick_resolution=tick_resolution,
        tracks=tracks,
        project_events=project_events,
        default_lyric=default_lyric,
        dynamics_breakpoints=dynamics_breakpoints)

    if debug:
        emit_log(f'Parsed the following project:\n{dumps(project)}\n', log_fn=log_fn)

    return project


def _quarter_note_bpm(mark: music21.tempo.MetronomeMark) -> float:
    """Normalize a metronome mark to quarter-note BPM."""
    if hasattr(mark, 'getQuarterBPM'):
        return float(mark.getQuarterBPM())
    return float(mark.number)