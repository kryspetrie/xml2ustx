from typing import List, cast, Set
from operator import itemgetter, attrgetter


import music21

from src.models.TimelineEvent import TimelineEvent
from src.models.TrackEvent import TrackEvent
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
    timeline_event_set: Set[TimelineEvent] = set()

    # Flatten all the different voices to distinct parts
    stream = stream.voicesToParts()

    # Loop over the parts and create Track list context
    for (index, part) in enumerate(stream.parts, 0):

        # Loop over supported events build Event list context
        track_events: List[TrackEvent] = []
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
                timeline_event_set.add(time_signature)

            if isinstance(event, music21.tempo.MetronomeMark):
                metronome_event: music21.tempo.MetronomeMark = cast(music21.tempo.MetronomeMark, event)
                tempo: Tempo = Tempo(position=metronome_event.offset, beat_per_minute=metronome_event.number)
                timeline_event_set.add(tempo)

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

    timeline_events: List[TimelineEvent] = sorted(timeline_event_set, key=attrgetter('position'))

    return Project(name=job.name,
                   tick_resolution=tick_resolution,
                   timeline_events=timeline_events,
                   tracks=tracks)