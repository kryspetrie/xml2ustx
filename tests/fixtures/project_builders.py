"""Build domain projects for component tests without MusicXML parsing."""
from __future__ import annotations

from src.domain.models.Note import Note
from src.domain.models.Project import Project
from src.domain.models.Tempo import Tempo
from src.domain.models.TimeSignature import TimeSignature
from src.domain.models.Track import Track
from src.domain.models.Voice import Voice


def default_voice() -> Voice:
    return Voice(renderer=None, phonemizer='OpenUtau.Core.DefaultPhonemizer', singer=None)


def single_track_project(
        *,
        name: str = 'Component Test',
        tick_resolution: int = 480,
        notes: list[tuple[float, float, int, str]] | None = None,
        default_lyric: str = 'doo',
        bpm: float = 120,
) -> Project:
    """Build a minimal project with one track and optional tempo/time signature."""
    note_events = [
        Note(position=position, duration=duration, tone=tone, lyrics=lyric)
        for position, duration, tone, lyric in (notes or [(0.0, 1.0, 60, 'la')])
    ]
    track = Track(
        name='Track 1',
        voice=default_voice(),
        pan=0.0,
        volume=0.0,
        events=note_events,
    )
    project_events = [
        TimeSignature(position=0, beat_per_bar=4, beat_unit=4),
        Tempo(position=0, beats_per_minute=bpm),
    ]
    return Project(
        name=name,
        tick_resolution=tick_resolution,
        tracks=[track],
        project_events=project_events,
        default_lyric=default_lyric,
    )


def multi_track_project(track_count: int = 2) -> Project:
    """Build a project with multiple tracks for header/voice-part tests."""
    tracks = []
    for index in range(track_count):
        tracks.append(
            Track(
                name=f'Track {index + 1}',
                voice=default_voice(),
                pan=float(index),
                volume=0.0,
                events=[Note(0.0, 1.0, 60 + index, f'n{index}')],
            )
        )
    return Project(
        name='Multi Track',
        tick_resolution=480,
        tracks=tracks,
        project_events=[Tempo(position=0, beats_per_minute=120)],
        default_lyric='doo',
    )
