"""Component-level USTX export tests built from domain models (no large MusicXML fixtures)."""
from __future__ import annotations

from pathlib import Path

import pytest

from src.application.ConfigParser import parse as parse_config
from src.application.ConfigPaths import resolve_config_file
from src.domain.ProjectParser import parse as parse_project
from src.ustx.UstxExport import write_to_string
from src.ustx.UstxSerializer import build_ustx_document, serialize_document
from tests.fixtures.project_builders import multi_track_project, single_track_project
from tests.ustx_compare import load_ustx_document


@pytest.fixture
def default_track_configs() -> tuple[list, str]:
    """Load the default bundled track configuration for tests."""
    config = parse_config(resolve_config_file(None))
    return config.track_config_map['default'], config.default_lyric or 'doo'


def test_build_document_from_domain_project() -> None:
    project = single_track_project(
        name='Component Test',
        tick_resolution=480,
        notes=[(0.0, 1.0, 60, 'la'), (1.0, 0.5, 62, '')],
        bpm=120,
    )
    document = build_ustx_document(project)
    assert document.ustx_version == 0.6
    assert document.name == 'Component Test'
    assert document.resolution == 480
    assert len(document.tracks) == 1
    assert len(document.voice_parts) == 1
    assert len(document.voice_parts[0].notes) == 2
    assert document.voice_parts[0].notes[1].lyric == 'doo'


def test_multi_track_project_exports_all_voice_parts() -> None:
    project = multi_track_project(track_count=3)
    document = build_ustx_document(project)
    assert len(document.tracks) == 3
    assert len(document.voice_parts) == 3


def test_serialize_document_matches_legacy_pipeline() -> None:
    """Structured serialization must match the public export entry point."""
    project = single_track_project()
    document = build_ustx_document(project)
    assert load_ustx_document(serialize_document(document)) == load_ustx_document(
        write_to_string(project)
    )


def test_note_uses_flow_style_pitch_and_vibrato() -> None:
    project = single_track_project()
    serialized = write_to_string(project)
    assert '{x: -40, y: 0, shape: io}' in serialized
    assert 'vibrato: {length: 0, period: 175, depth: 25, in: 10, out: 10, shift: 0, drift: 0}' in serialized


def test_minimal_musicxml_end_to_end(
        minimal_xml: Path,
        default_track_configs: tuple[list, str]) -> None:
    """Single integration check that parsing and export stay wired together."""
    track_configs, default_lyric = default_track_configs
    project = parse_project(
        str(minimal_xml),
        'Minimal',
        track_configs,
        default_lyric,
        debug=False,
    )
    serialized = write_to_string(project)
    assert 'name: Minimal' in serialized
    assert 'lyric: "la"' in serialized or 'lyric: la' in serialized
