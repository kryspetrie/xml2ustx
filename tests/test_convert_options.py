"""Tests for convert options builder."""
from __future__ import annotations

from pathlib import Path

import pytest

from src.ui.native.convert_options import build_native_ui_options
from src.ui.native.models.convert_form_state import ConvertFormState, CustomTrackRow


def test_build_options_requires_input() -> None:
    with pytest.raises(ValueError, match='Add at least one input file'):
        build_native_ui_options(ConvertFormState(), None)


def test_build_options_single_file(minimal_xml: Path) -> None:
    state = ConvertFormState(input_files=[str(minimal_xml)])
    options = build_native_ui_options(state, None)
    assert options.input_files == [str(minimal_xml)]


def test_build_options_custom_tracks_validates_voice(minimal_xml: Path) -> None:
    state = ConvertFormState(
        input_files=[str(minimal_xml)],
        use_custom_tracks=True,
        custom_tracks=[CustomTrackRow(name='T1', voice_id='not-a-real-voice')],
    )
    with pytest.raises(ValueError, match='Unknown voice id'):
        build_native_ui_options(state, None)


def test_build_options_custom_tracks_requires_rows(minimal_xml: Path) -> None:
    state = ConvertFormState(
        input_files=[str(minimal_xml)],
        use_custom_tracks=True,
        custom_tracks=[],
    )
    with pytest.raises(ValueError, match='Add at least one custom track row'):
        build_native_ui_options(state, None)
