"""Unit tests for structured USTX model classes."""
from __future__ import annotations

from src.domain.models.Note import Note
from src.domain.models.Voice import Voice
from src.domain.models.Track import Track
from src.ustx.models.expression import UstxExpression, UstxExpressionCatalog
from src.ustx.models.note import UstxNote, UstxPitchCurve, UstxVibrato
from src.ustx.models.track import UstxTrackHeader
from src.ustx.models.yaml_types import FlowMap, QuotedStr


def test_expression_catalog_loads_default_definitions() -> None:
    catalog = UstxExpressionCatalog.load_default()
    assert 'dyn' in catalog.expressions
    assert catalog.expressions['dyn'].type == 'Curve'
    assert catalog.expressions['eng'].options == ('', 'worldline')


def test_expression_round_trip_mapping() -> None:
    expression = UstxExpression(
        name='velocity',
        abbr='vel',
        type='Numerical',
        min=0,
        max=200,
        default_value=100,
        is_flag=False,
        flag='',
    )
    restored = UstxExpression.from_mapping(expression.to_mapping())
    assert restored == expression


def test_expression_omits_missing_flag_key() -> None:
    expression = UstxExpression(
        name='voice color',
        abbr='clr',
        type='Options',
        min=0,
        max=-1,
        default_value=0,
        is_flag=False,
        options=(),
    )
    assert 'flag' not in expression.to_mapping()


def test_note_from_domain_uses_default_lyric() -> None:
    note = Note(position=0.0, duration=1.0, tone=60, lyrics='')
    ustx_note = UstxNote.from_domain(note, tick_resolution=100, default_lyric='doo')
    assert ustx_note.lyric == 'doo'
    assert ustx_note.position == 0
    assert ustx_note.duration == 100


def test_note_to_mapping_quotes_lyrics() -> None:
    ustx_note = UstxNote.from_domain(
        Note(position=0.0, duration=1.0, tone=60, lyrics='la'),
        tick_resolution=100,
        default_lyric='doo',
    )
    mapping = ustx_note.to_mapping()
    assert isinstance(mapping['lyric'], QuotedStr)
    assert isinstance(mapping['vibrato'], FlowMap)
    assert mapping['pitch']['data'][0]['shape'] == 'io'


def test_track_header_preserves_legacy_none_name() -> None:
    voice = Voice(renderer=None, phonemizer='OpenUtau.Core.DefaultPhonemizer', singer=None)
    track = Track(name=None, voice=voice, pan=0.0, volume=0.0, events=[])
    header = UstxTrackHeader.from_domain(track)
    assert header.track_name == 'None'


def test_default_pitch_and_vibrato_values() -> None:
    pitch = UstxPitchCurve.default()
    vibrato = UstxVibrato.default()
    assert len(pitch.data) == 2
    assert vibrato.to_yaml()['in'] == 10
    assert vibrato.to_yaml()['period'] == 175
