from typing import List, Optional, cast

import src.ustx.UstxFormatHelpers as Ustx
from src.models.Note import Note
from src.models.Project import Project
from src.models.Tempo import Tempo
from src.models.TimeSignature import TimeSignature
from src.models.Event import Event


def export(project: Project, outfile: str):
    with open(outfile, 'w') as f:
        ustx: str = write_to_string(project)
        f.write(ustx)


def write_to_string(project: Project):

    # Get time signatures and tempos across all tracks
    time_signatures: List[TimeSignature] = project.find_unique_time_signatures()
    tempos: List[Tempo] = project.find_unique_tempos()

    ustx_fragments: List[str] = [__header(project)]
    ustx_fragments += __tracks(project)
    ustx_fragments += __tempos(tempos, project.tick_resolution)
    ustx_fragments += __time_signatures(time_signatures, project.tick_resolution)
    ustx_fragments += __voices(project)
    ustx_fragments += [Ustx.EMPTY_WAVE_PARTS]
    return '\n'.join(ustx_fragments)


def __tempos(tempos: List[Tempo], tick_resolution: int) -> List[str]:
    tempo_fragments: List[str] = []
    if tempos is not None and len(tempos) > 0:
        tempo_fragments.append(Ustx.TEMPOS_LABEL)
        for tempo in tempos:
            position: int = int(tempo.position * tick_resolution)
            tempo_fragments.append(Ustx.format_tempo(position, tempo.beat_per_minute))
    return tempo_fragments


def __time_signatures(time_signatures: List[TimeSignature], tick_resolution: int) -> List[str]:
    time_signature_fragments: List[str] = []
    if time_signatures is not None and len(time_signatures) > 0:
        time_signature_fragments.append(Ustx.TIME_SIGNATURES_LABEL)
        for time_signature in time_signatures:
            position: int = int(time_signature.position * tick_resolution)
            time_signature_fragments.append(
                Ustx.format_time_signature(position, time_signature.beat_per_bar, time_signature.beat_unit))
    return time_signature_fragments


def __tracks(project: Project) -> List[str]:
    ustx_fragments: List[str] = [Ustx.TRACKS_LABEL]

    for track in project.tracks:
        header_string: str = Ustx.format_track_header(
            name=track.name,
            phonemizer=track.voice.phonemizer,
            singer=track.voice.singer,
            renderer=track.voice.renderer,
            volume=track.volume,
            pan=track.pan)
        ustx_fragments.append(header_string)

    return ustx_fragments


def __voices(project: Project) -> List[str]:
    ustx_fragments: List[str] = [Ustx.VOICE_PARTS_LABEL]
    for index, track in enumerate(project.tracks, 0):
        track_string: str = Ustx.generate_part(track_name=track.name, track_number=index)
        ustx_fragments.append(track_string)
        for event in track.events:
            note_string: str = __event(event=event, tick_resolution=project.tick_resolution)
            if note_string is not None:
                ustx_fragments.append(note_string)

    return ustx_fragments


def __event(event: Event, tick_resolution: int) -> Optional[str]:
    if not isinstance(event, Note):
        return None

    note_event: Note = cast(Note, event)
    tick_position: int = int(note_event.position * tick_resolution)
    tick_duration: int = int(note_event.duration * tick_resolution)

    return Ustx.format_note(tick_position=tick_position,
                            tick_duration=tick_duration,
                            tone=note_event.tone,
                            lyric=note_event.lyric)


def __header(project: Project) -> str:
    return Ustx.format_file_header(name=project.name, resolution=project.tick_resolution)
