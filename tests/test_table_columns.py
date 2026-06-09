"""Tests for native UI table column helpers."""
from __future__ import annotations

from PySide6.QtWidgets import QHeaderView, QTableView

from src.ui.native.config_form_editor import TrackPresetModel
from src.ui.native.table_columns import (
    TRACK_TABLE_COLUMN_MIN_WIDTHS,
    configure_track_table_columns,
    refresh_table_column_sizes,
)


def test_track_table_columns_do_not_stretch_first_column(qtbot) -> None:
    model = TrackPresetModel()
    model.add_row('default')
    table = QTableView()
    table.setModel(model)
    qtbot.addWidget(table)
    configure_track_table_columns(table)
    table.show()
    qtbot.waitExposed(table)

    header = table.horizontalHeader()
    assert header.sectionResizeMode(0) != QHeaderView.ResizeMode.Stretch
    assert header.sectionResizeMode(2) != QHeaderView.ResizeMode.Stretch
    assert header.sectionSize(0) >= TRACK_TABLE_COLUMN_MIN_WIDTHS[0]
    assert header.sectionSize(2) >= TRACK_TABLE_COLUMN_MIN_WIDTHS[2]


def test_refresh_table_column_sizes_enforces_minimums(qtbot) -> None:
    model = TrackPresetModel()
    model.add_row('default')
    table = QTableView()
    table.setModel(model)
    qtbot.addWidget(table)
    configure_track_table_columns(table)

    header = table.horizontalHeader()
    header.resizeSection(2, 20)
    refresh_table_column_sizes(table)
    assert header.sectionSize(2) >= TRACK_TABLE_COLUMN_MIN_WIDTHS[2]
