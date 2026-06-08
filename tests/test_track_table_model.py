"""Tests for custom track table model."""
from __future__ import annotations

from src.ui.native.track_table_model import TrackTableModel


def test_track_model_add_and_edit() -> None:
    model = TrackTableModel(['default', 'tiger'])
    model.add_row('Lead')
    assert model.rowCount() == 1
    assert model.rows()[0].name == 'Lead'
    assert model.rows()[0].voice_id == 'default'

    index = model.index(0, 2)
    assert model.setData(index, 5.0)
    assert model.rows()[0].pan == 5.0


def test_track_model_remove_row() -> None:
    model = TrackTableModel(['default'])
    model.add_row()
    model.add_row()
    model.remove_row(0)
    assert model.rowCount() == 1


def test_track_model_voice_ids_update() -> None:
    model = TrackTableModel(['a'])
    model.set_voice_ids(['x', 'y'])
    assert model.voice_ids() == ['x', 'y']
