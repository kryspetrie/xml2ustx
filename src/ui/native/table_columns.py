"""Shared table column sizing helpers for the native UI."""
from __future__ import annotations

from collections.abc import Mapping

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QHeaderView, QTableView

DEFAULT_CELL_PADDING_PX = 8

TRACK_TABLE_COLUMN_MIN_WIDTHS: dict[int, int] = {
    0: 120,
    1: 100,
    2: 88,
    3: 88,
}


def configure_content_aware_columns(
        table: QTableView,
        *,
        stretch_column: int | None = None,
        column_minimum_widths: Mapping[int, int] | None = None,
        cell_padding_px: int = DEFAULT_CELL_PADDING_PX) -> None:
    """Size columns from their contents, with optional stretch and minimum widths."""
    header = table.horizontalHeader()
    header.setStretchLastSection(False)
    header.setSectionsMovable(False)

    table._column_minimum_widths = dict(column_minimum_widths or {})  # type: ignore[attr-defined]
    table._stretch_column = stretch_column  # type: ignore[attr-defined]

    column_count = table.model().columnCount() if table.model() is not None else 0
    for column in range(column_count):
        if stretch_column is not None and column == stretch_column:
            header.setSectionResizeMode(column, QHeaderView.ResizeMode.Stretch)
        else:
            header.setSectionResizeMode(column, QHeaderView.ResizeMode.ResizeToContents)

    table.setWordWrap(False)
    _apply_table_cell_padding(table, cell_padding_px)
    refresh_table_column_sizes(table)

    model = table.model()
    if model is not None:
        model.modelReset.connect(lambda: _schedule_table_column_refresh(table))
        model.rowsInserted.connect(lambda *_args: _schedule_table_column_refresh(table))
        model.rowsRemoved.connect(lambda *_args: _schedule_table_column_refresh(table))


def _schedule_table_column_refresh(table: QTableView) -> None:
    QTimer.singleShot(0, lambda: refresh_table_column_sizes(table))


def refresh_table_column_sizes(table: QTableView) -> None:
    """Recompute content-based widths and enforce per-column minimums."""
    header = table.horizontalHeader()
    model = table.model()
    if model is None:
        return

    minimum_widths: dict[int, int] = getattr(table, '_column_minimum_widths', {})
    stretch_column: int | None = getattr(table, '_stretch_column', None)

    for column in range(model.columnCount()):
        if stretch_column is not None and column == stretch_column:
            continue
        table.resizeColumnToContents(column)
        width = header.sectionSize(column)
        min_width = minimum_widths.get(column, 0)
        if min_width:
            width = max(width, min_width)
        header.setSectionResizeMode(column, QHeaderView.ResizeMode.Interactive)
        header.resizeSection(column, width)


def configure_track_table_columns(table: QTableView) -> None:
    """Configure a four-column track preset/custom track table."""
    configure_content_aware_columns(
        table,
        stretch_column=None,
        column_minimum_widths=TRACK_TABLE_COLUMN_MIN_WIDTHS,
    )


def _apply_table_cell_padding(table: QTableView, padding_px: int) -> None:
    table.setObjectName('paddedTableView')
    table.horizontalHeader().setStyleSheet(
        f'QHeaderView::section {{ padding-left: {padding_px}px; padding-right: {padding_px}px; }}',
    )
