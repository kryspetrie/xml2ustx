"""Table model for custom per-track settings."""
from __future__ import annotations

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt

from src.ui.native.models.convert_form_state import CustomTrackRow


class TrackTableModel(QAbstractTableModel):
    """Model/view backing store for custom track rows."""

    HEADERS = ('Track name', 'Voice id', 'Pan', 'Volume')

    def __init__(self, voice_ids: list[str] | None = None, parent=None):
        super().__init__(parent)
        self._voice_ids = list(voice_ids or [])
        self._rows: list[CustomTrackRow] = []

    def voice_ids(self) -> list[str]:
        """Return configured voice ids for combo delegates."""
        return list(self._voice_ids)

    def set_voice_ids(self, voice_ids: list[str]) -> None:
        """Replace voice ids after config reload."""
        self._voice_ids = list(voice_ids)
        self.layoutChanged.emit()

    def rows(self) -> list[CustomTrackRow]:
        """Return a copy of current track rows."""
        return list(self._rows)

    def add_row(self, name: str | None = None) -> None:
        """Append a track row with defaults."""
        row_number = len(self._rows) + 1
        default_voice = self._voice_ids[0] if self._voice_ids else ''
        self.beginInsertRows(QModelIndex(), len(self._rows), len(self._rows))
        self._rows.append(CustomTrackRow(
            name=name or f'Track {row_number}',
            voice_id=default_voice,
        ))
        self.endInsertRows()

    def remove_row(self, row: int) -> None:
        """Remove a track row by index."""
        if row < 0 or row >= len(self._rows):
            return
        self.beginRemoveRows(QModelIndex(), row, row)
        del self._rows[row]
        self.endRemoveRows()

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: N802
        if parent.isValid():
            return 0
        return len(self._rows)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: N802
        if parent.isValid():
            return 0
        return len(self.HEADERS)

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole):  # noqa: N802,E501
        if role != Qt.ItemDataRole.DisplayRole or orientation != Qt.Orientation.Horizontal:
            return None
        if 0 <= section < len(self.HEADERS):
            return self.HEADERS[section]
        return None

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole):  # noqa: N802
        if not index.isValid() or not (0 <= index.row() < len(self._rows)):
            return None
        row = self._rows[index.row()]
        if role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole):
            if index.column() == 0:
                return row.name
            if index.column() == 1:
                return row.voice_id
            if index.column() == 2:
                return row.pan
            if index.column() == 3:
                return row.volume
        return None

    def setData(self, index: QModelIndex, value, role: int = Qt.ItemDataRole.EditRole) -> bool:  # noqa: N802
        if role != Qt.ItemDataRole.EditRole or not index.isValid():
            return False
        row = self._rows[index.row()]
        if index.column() == 0:
            row.name = str(value)
        elif index.column() == 1:
            row.voice_id = str(value)
        elif index.column() == 2:
            row.pan = float(value)
        elif index.column() == 3:
            row.volume = float(value)
        else:
            return False
        self.dataChanged.emit(index, index, [Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole])
        return True

    def flags(self, index: QModelIndex) -> Qt.ItemFlag:  # noqa: N802
        if not index.isValid():
            return Qt.ItemFlag.NoItemFlags
        return (
            Qt.ItemFlag.ItemIsEnabled
            | Qt.ItemFlag.ItemIsSelectable
            | Qt.ItemFlag.ItemIsEditable
        )
