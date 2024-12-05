from typing import List, cast

import music21

from src.models.Event import Event
from src.models.Tempo import Tempo
from src.models.TimeSignature import TimeSignature
from src.models.TrackConfig import TrackConfig
from src.models.Note import Note
from src.models.Track import Track
from src.models.Project import Project
from src.models.JobConfig import JobConfig


def parse(job: JobConfig):
    stream = music21.converter.parse(job.input_file)

    # This is a concept in MIDI and USTX, but not MusicXML
    tick_resolution = music21.defaults.ticksPerQuarter

    tracks: List[Track] = []

    # Flatten all the different voices to distinct parts
    stream = stream.voicesToParts()

    # Unroll notated repeats
    stream = stream.expandRepeats()

    # Extend all tied notes into joined objects (e.g. ignore measure divisions)
    stream.stripTies(inPlace=True, matchByPitch=True)

    # TODO: detect swing annotation and quantize appropriately

    # Loop over the parts and create Track list context
    for (index, part) in enumerate(stream.parts, 0):

        # Loop over supported events build Event list context
        track_events: List[Event] = []
        for event in part.flat:

            # Add note events
            if isinstance(event, music21.note.Note) and event.isNote:
                note_event: music21.note.Note = cast(music21.note.Note, event)
                note: Note = Note(position=note_event.offset,
                                  duration=note_event.quarterLength,
                                  tone=note_event.pitch.midi,
                                  lyrics=note_event.lyric)
                track_events.append(note)

            # Add time signature events
            if isinstance(event, music21.meter.TimeSignature):
                time_signature_event: music21.meter.TimeSignature = cast(music21.meter.TimeSignature, event)
                time_signature: TimeSignature = TimeSignature(
                    position=time_signature_event.offset,
                    beat_per_bar=time_signature_event.numerator,
                    beat_unit=time_signature_event.denominator)
                track_events.append(time_signature)

            if isinstance(event, music21.tempo.MetronomeMark):
                metronome_event: music21.tempo.MetronomeMark = cast(music21.tempo.MetronomeMark, event)
                tempo: Tempo = Tempo(position=metronome_event.offset, beat_per_minute=metronome_event.number)
                track_events.append(tempo)

        # If we have a specific track config for this track, use it. Otherwise, default to first config.
        track_config: TrackConfig = job.track_configs[index] \
            if index < len(job.track_configs) \
            else job.track_configs[0]

        # Override the track name if specified in the config
        track_name = track_config.name \
            if (track_config.name is not None or track_config.name != "") \
            else part.partName

        track: Track = Track(name=track_name,
                             voice=track_config.voice,
                             pan=track_config.pan,
                             volume=track_config.volume,
                             events=track_events)
        tracks.append(track)

    return Project(name=job.name,
                   tick_resolution=tick_resolution,
                   tracks=tracks,
                   default_lyric=job.default_lyric)
