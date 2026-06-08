"""Shared table column sizing helpers for the native UI."""
from __future__ import annotations

from PySide6.QtWidgets import QHeaderView, QTableView


def configure_content_aware_columns(table: QTableView, stretch_column: int) -> None:
    """Size columns to their contents and stretch one column to fill the table width."""
    header = table.horizontalHeader()
    header.setStretchLastSection(False)
    header.setSectionsMovable(False)

    column_count = table.model().columnCount() if table.model() is not None else 0
    for column in range(column_count):
        if column == stretch_column:
            header.setSectionResizeMode(column, QHeaderView.ResizeMode.Stretch)
        else:
            header.setSectionResizeMode(column, QHeaderView.ResizeMode.ResizeToContents)

    table.setWordWrap(False)
