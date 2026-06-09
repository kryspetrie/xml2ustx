"""Tests for score-driven swing and groove detection."""
from __future__ import annotations

from pathlib import Path

import pytest

from src.application.ConfigParser import parse as parse_config
from src.application.ConfigPaths import resolve_config_file
from src.domain.ProjectParser import parse as parse_project
from src.domain.models.Note import Note
from src.domain.rhythm_config import RhythmConfig
from src.domain.score_rhythm_detection import (
    is_rhythm_annotation_text,
    resolve_rhythm_rules,
    score_has_groove_annotation,
    score_has_swing_annotation,
)
from src.ustx.UstxExport import write_to_string
from tests.ustx_compare import assert_consecutive_notes_abut, assert_note_durations_beats, load_ustx_document


def test_is_rhythm_annotation_text() -> None:
    assert is_rhythm_annotation_text('Swing')
    assert is_rhythm_annotation_text('apply groove')
    assert not is_rhythm_annotation_text('no swing')
    assert not is_rhythm_annotation_text('no groove')


def test_resolve_rules_respects_disable() -> None:
    config = RhythmConfig(rhythm_disabled=True, force_swing=True, swing_intensity=100)
    assert resolve_rhythm_rules(config, has_swing_annotation=True, has_groove_annotation=False) == []


def test_resolve_rules_force_swing_without_score_marking() -> None:
    config = RhythmConfig(force_swing=True, swing_intensity=100)
    rules = resolve_rhythm_rules(config, has_swing_annotation=False, has_groove_annotation=False)
    assert len(rules) == 1


def test_resolve_rules_force_groove_without_score_marking() -> None:
    config = RhythmConfig(force_groove=True, groove='8th: 2/3 1/3')
    rules = resolve_rhythm_rules(config, has_swing_annotation=False, has_groove_annotation=False)
    assert len(rules) == 1


def test_resolve_rules_uses_groove_when_marked() -> None:
    config = RhythmConfig(groove='8th: 2/3 1/3', swing_intensity=100)
    rules = resolve_rhythm_rules(config, has_swing_annotation=True, has_groove_annotation=True)
    assert len(rules) == 1
    assert rules[0].note_length == 0.5


def test_score_has_swing_annotation_ignores_title_and_lyrics(tmp_path: Path) -> None:
    xml = tmp_path / 'lyric-swing.musicxml'
    xml.write_text(
        '''<?xml version="1.0" encoding="UTF-8"?>
<score-partwise version="3.1">
  <work><work-title>Swing Low</work-title></work>
  <part-list><score-part id="P1"><part-name>Voice</part-name></score-part></part-list>
  <part id="P1">
    <measure number="1">
      <attributes><divisions>1</divisions><key><fifths>0</fifths></key>
        <time><beats>4</beats><beat-type>4</beat-type></time></attributes>
      <note><pitch><step>C</step><octave>4</octave></pitch><duration>1</duration><type>quarter</type>
        <lyric number="1"><syllabic>single</syllabic><text>swing</text></lyric></note>
    </measure>
  </part>
</score-partwise>''',
        encoding='utf-8',
    )
    import music21
    stream = music21.converter.parse(str(xml)).expandRepeats()
    assert score_has_swing_annotation(stream, stream.flatten()) is False


def test_score_has_swing_annotation_not_blocked_by_swing_filename(tmp_path: Path) -> None:
    xml = tmp_path / 'swing.musicxml'
    xml.write_text(_eighth_pair_xml(with_swing_direction=True), encoding='utf-8')

    import music21
    stream = music21.converter.parse(str(xml)).expandRepeats()
    assert score_has_swing_annotation(stream, stream.flatten()) is True


def test_parse_applies_swing_when_score_marked(tmp_path: Path) -> None:
    xml = tmp_path / 'swing.musicxml'
    xml.write_text(_eighth_pair_xml(with_swing_direction=True), encoding='utf-8')

    config = parse_config(resolve_config_file(None))
    project = parse_project(
        str(xml),
        'Swing',
        config.track_config_map['default'],
        'la',
        rhythm_config=RhythmConfig(force_swing=False, swing_intensity=100),
    )
    durations = [note.duration for note in project.tracks[0].events if isinstance(note, Note)]
    assert durations[0] == pytest.approx(2 / 3)
    assert durations[1] == pytest.approx(1 / 3)


def test_parse_skips_swing_when_disabled_even_with_marking(tmp_path: Path) -> None:
    xml = tmp_path / 'swing.musicxml'
    xml.write_text(_eighth_pair_xml(with_swing_direction=True), encoding='utf-8')

    config = parse_config(resolve_config_file(None))
    project = parse_project(
        str(xml),
        'Disabled',
        config.track_config_map['default'],
        'la',
        rhythm_config=RhythmConfig(rhythm_disabled=True, swing_intensity=100),
    )
    durations = [note.duration for note in project.tracks[0].events if isinstance(note, Note)]
    assert durations == [pytest.approx(0.5), pytest.approx(0.5)]


def test_parse_applies_force_swing_without_marking(tmp_path: Path) -> None:
    xml = tmp_path / 'plain.musicxml'
    xml.write_text(_eighth_pair_xml(with_swing_direction=False), encoding='utf-8')

    config = parse_config(resolve_config_file(None))
    project = parse_project(
        str(xml),
        'Forced',
        config.track_config_map['default'],
        'la',
        rhythm_config=RhythmConfig(force_swing=True, swing_intensity=100),
    )
    durations = [note.duration for note in project.tracks[0].events if isinstance(note, Note)]
    assert durations[0] == pytest.approx(2 / 3)


def test_swing_exported_ustx_note_durations_match_expected_math(tmp_path: Path) -> None:
    xml = tmp_path / 'swing.musicxml'
    xml.write_text(_eighth_pair_xml(with_swing_direction=True), encoding='utf-8')

    config = parse_config(resolve_config_file(None))
    project = parse_project(
        str(xml),
        'Swing USTX',
        config.track_config_map['default'],
        'la',
        rhythm_config=RhythmConfig(force_swing=False, swing_intensity=100),
    )

    document = load_ustx_document(write_to_string(project))
    assert_note_durations_beats(document, [2 / 3, 1 / 3])
    assert_consecutive_notes_abut(document)


def _eighth_pair_xml(*, with_swing_direction: bool) -> str:
    direction = ''
    if with_swing_direction:
        direction = '<direction placement="above"><direction-type><words>Swing</words></direction-type></direction>'
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<score-partwise version="3.1">
  <part-list><score-part id="P1"><part-name>Voice</part-name></score-part></part-list>
  <part id="P1">
    <measure number="1">
      <attributes><divisions>2</divisions><key><fifths>0</fifths></key>
        <time><beats>4</beats><beat-type>4</beat-type></time></attributes>
      {direction}
      <note><pitch><step>C</step><octave>4</octave></pitch><duration>1</duration><type>eighth</type>
        <lyric number="1"><syllabic>single</syllabic><text>la</text></lyric></note>
      <note><pitch><step>D</step><octave>4</octave></pitch><duration>1</duration><type>eighth</type>
        <lyric number="1"><syllabic>single</syllabic><text>la</text></lyric></note>
    </measure>
  </part>
</score-partwise>'''
