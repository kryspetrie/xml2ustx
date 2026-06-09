"""Tests for newly implemented MusicXML score features."""
from __future__ import annotations

from pathlib import Path

import music21
import pytest

from src.application.ConfigParser import parse as parse_config
from src.application.ConfigPaths import resolve_config_file
from src.domain.ProjectParser import parse as parse_project
from src.domain.dynamics_parser import parse_dynamics, scalar_to_dyn
from src.domain.lyric_helpers import fill_missing_lyrics, merge_syllabic_lyrics_in_part
from src.domain.models.Note import Note
from src.domain.models.Track import Track
from src.domain.rhythm_config import RhythmConfig
from src.ustx.UstxExport import write_to_string
from src.ustx.UstxSerializer import build_ustx_document
from tests.fixtures.project_builders import default_voice


def test_scalar_to_dyn_maps_mf_to_zero() -> None:
    assert scalar_to_dyn(0.55) == 0


def test_parse_applies_configured_swing(tmp_path: Path) -> None:
    xml = tmp_path / 'eighths.musicxml'
    xml.write_text(
        '''<?xml version="1.0" encoding="UTF-8"?>
<score-partwise version="3.1">
  <part-list><score-part id="P1"><part-name>Voice</part-name></score-part></part-list>
  <part id="P1">
    <measure number="1">
      <attributes><divisions>2</divisions><key><fifths>0</fifths></key>
        <time><beats>4</beats><beat-type>4</beat-type></time></attributes>
      <note><pitch><step>C</step><octave>4</octave></pitch><duration>1</duration><type>eighth</type>
        <lyric number="1"><syllabic>single</syllabic><text>la</text></lyric></note>
      <note><pitch><step>D</step><octave>4</octave></pitch><duration>1</duration><type>eighth</type>
        <lyric number="1"><syllabic>single</syllabic><text>la</text></lyric></note>
    </measure>
  </part>
</score-partwise>''',
        encoding='utf-8',
    )
    config = parse_config(resolve_config_file(None))
    track_configs = config.track_config_map['default']
    rhythm = RhythmConfig(force_swing=True, swing_intensity=100)

    project = parse_project(
        str(xml),
        'Swing',
        track_configs,
        config.default_lyric or 'doo',
        rhythm_config=rhythm,
    )

    durations = [note.duration for note in project.tracks[0].events if isinstance(note, Note)]
    assert durations[0] == pytest.approx(2 / 3)
    assert durations[1] == pytest.approx(1 / 3)


def test_merge_syllabic_lyrics_joins_begin_end() -> None:
    part = music21.stream.Part()
    begin = music21.note.Note('C4', quarterLength=1.0)
    begin.lyrics = [music21.note.Lyric(text='ve', syllabic='begin')]
    end = music21.note.Note('D4', quarterLength=1.0)
    end.lyrics = [music21.note.Lyric(text='ry', syllabic='end')]
    part.insert(0, begin)
    part.insert(1, end)

    merge_syllabic_lyrics_in_part(part)
    assert begin.lyric == 'very'
    assert end.lyric == '+'


def test_fill_missing_lyrics_from_other_parts() -> None:
    tracks = [
        Track(
            name='Lead',
            voice=default_voice(),
            pan=0.0,
            volume=0.0,
            events=[Note(position=0.0, duration=1.0, tone=60, lyrics='la')],
        ),
        Track(
            name='Harmony',
            voice=default_voice(),
            pan=0.0,
            volume=0.0,
            events=[Note(position=0.0, duration=1.0, tone=64, lyrics='')],
        ),
    ]
    fill_missing_lyrics(tracks, default_lyric='')
    assert tracks[1].events[0].lyric == 'la'


def test_parse_dynamics_from_score(tmp_path: Path) -> None:
    xml = tmp_path / 'dynamics.musicxml'
    xml.write_text(
        '''<?xml version="1.0" encoding="UTF-8"?>
<score-partwise version="3.1">
  <part-list><score-part id="P1"><part-name>Voice</part-name></score-part></part-list>
  <part id="P1">
    <measure number="1">
      <attributes><divisions>1</divisions><key><fifths>0</fifths></key>
        <time><beats>4</beats><beat-type>4</beat-type></time></attributes>
      <direction placement="below"><direction-type><dynamics><f/></dynamics></direction-type></direction>
      <note><pitch><step>C</step><octave>4</octave></pitch><duration>1</duration><type>quarter</type>
        <lyric number="1"><syllabic>single</syllabic><text>la</text></lyric></note>
    </measure>
  </part>
</score-partwise>''',
        encoding='utf-8',
    )
    stream = music21.converter.parse(str(xml))
    breakpoints = parse_dynamics(stream.flatten())
    assert breakpoints
    assert breakpoints[0].dyn_value > 0


def test_export_includes_dyn_curve(tmp_path: Path) -> None:
    xml = tmp_path / 'dynamics.musicxml'
    xml.write_text(
        '''<?xml version="1.0" encoding="UTF-8"?>
<score-partwise version="3.1">
  <part-list><score-part id="P1"><part-name>Voice</part-name></score-part></part-list>
  <part id="P1">
    <measure number="1">
      <attributes><divisions>1</divisions><key><fifths>0</fifths></key>
        <time><beats>4</beats><beat-type>4</beat-type></time></attributes>
      <direction placement="below"><direction-type><dynamics><mf/></dynamics></direction-type></direction>
      <note><pitch><step>C</step><octave>4</octave></pitch><duration>1</duration><type>quarter</type>
        <lyric number="1"><syllabic>single</syllabic><text>la</text></lyric></note>
    </measure>
  </part>
</score-partwise>''',
        encoding='utf-8',
    )
    config = parse_config(resolve_config_file(None))
    project = parse_project(
        str(xml),
        'Dynamics',
        config.track_config_map['default'],
        config.default_lyric or 'doo',
    )
    document = build_ustx_document(project)
    assert document.voice_parts[0].curves
    assert document.voice_parts[0].curves[0].abbr == 'dyn'

    serialized = write_to_string(project)
    assert 'curves:' in serialized
    assert 'abbr: dyn' in serialized


def test_parse_fills_missing_lyrics_with_builtin_default(
        minimal_xml: Path,
        tmp_path: Path,
) -> None:
    text = minimal_xml.read_text(encoding='utf-8')
    text = text.replace('<text>lo</text>', '<text></text>')
    broken = tmp_path / 'no-lyric.musicxml'
    broken.write_text(text, encoding='utf-8')

    config = parse_config(resolve_config_file(None))
    track_configs = config.track_config_map['default']

    project = parse_project(
        str(broken),
        'Broken',
        track_configs,
        '',
    )

    assert project.tracks[0].events[1].lyric == 'doo'
