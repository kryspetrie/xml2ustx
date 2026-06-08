"""Visual form editor for xml2ustx configuration."""
from __future__ import annotations

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt, Signal
from PySide6.QtWidgets import (
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from src.ui.native.config_data import (
    ConfigDocument,
    TrackConfigRow,
    TrackPresetRow,
    VoiceConfigRow,
    parse_config_document,
    serialize_config_document,
)
from src.ui.native.table_columns import configure_content_aware_columns
from src.ui.native.track_delegates import DoubleSpinDelegate


class VoiceConfigModel(QAbstractTableModel):
    """Table model for voice presets."""

    HEADERS = ('Voice id', 'Singer', 'Renderer', 'Phonemizer')

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._rows: list[VoiceConfigRow] = []

    def set_rows(self, rows: list[VoiceConfigRow]) -> None:
        self.beginResetModel()
        self._rows = list(rows)
        self.endResetModel()

    def rows(self) -> list[VoiceConfigRow]:
        return list(self._rows)

    def add_row(self) -> None:
        row_number = len(self._rows) + 1
        self.beginInsertRows(QModelIndex(), len(self._rows), len(self._rows))
        self._rows.append(VoiceConfigRow(voice_id=f'voice-{row_number}'))
        self.endInsertRows()

    def remove_row(self, row: int) -> None:
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
                return row.voice_id
            if index.column() == 1:
                return row.singer
            if index.column() == 2:
                return row.renderer
            if index.column() == 3:
                return row.phonemizer
        return None

    def setData(self, index: QModelIndex, value, role: int = Qt.ItemDataRole.EditRole) -> bool:  # noqa: N802
        if role != Qt.ItemDataRole.EditRole or not index.isValid():
            return False
        row = self._rows[index.row()]
        if index.column() == 0:
            row.voice_id = str(value)
        elif index.column() == 1:
            row.singer = str(value)
        elif index.column() == 2:
            row.renderer = str(value)
        elif index.column() == 3:
            row.phonemizer = str(value)
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


class TrackPresetModel(QAbstractTableModel):
    """Table model for tracks inside the selected preset."""

    HEADERS = ('Track name', 'Voice id', 'Pan', 'Volume')

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._rows: list[TrackConfigRow] = []

    def set_rows(self, rows: list[TrackConfigRow]) -> None:
        self.beginResetModel()
        self._rows = list(rows)
        self.endResetModel()

    def rows(self) -> list[TrackConfigRow]:
        return list(self._rows)

    def add_row(self, voice_id: str = '') -> None:
        row_number = len(self._rows) + 1
        self.beginInsertRows(QModelIndex(), len(self._rows), len(self._rows))
        self._rows.append(TrackConfigRow(
            voice_id=voice_id,
            track_name=f'Track {row_number}',
        ))
        self.endInsertRows()

    def remove_row(self, row: int) -> None:
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
                return row.track_name
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
            row.track_name = str(value)
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


class ConfigFormEditor(QWidget):
    """Structured editor for voice and track configuration."""

    changed = Signal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._presets: list[TrackPresetRow] = []
        self._block_change = False
        self._build_ui()
        self._wire_change_signals()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        lyric_row = QFormLayout()
        self.default_lyric = QLineEdit()
        self.default_lyric.setAccessibleName(self.tr('Default lyric'))
        lyric_row.addRow(self.tr('Default lyric'), self.default_lyric)
        layout.addLayout(lyric_row)

        voices_group = QGroupBox(self.tr('Voice presets'))
        voices_layout = QVBoxLayout(voices_group)
        self.voice_model = VoiceConfigModel(self)
        self.voice_table = QTableView()
        self.voice_table.setModel(self.voice_model)
        configure_content_aware_columns(self.voice_table, stretch_column=3)
        self.voice_table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        voices_layout.addWidget(self.voice_table)

        voice_btn_row = QHBoxLayout()
        add_voice_btn = QPushButton(self.tr('Add voice'))
        add_voice_btn.clicked.connect(self._add_voice)
        remove_voice_btn = QPushButton(self.tr('Remove voice'))
        remove_voice_btn.clicked.connect(self._remove_voice)
        voice_btn_row.addWidget(add_voice_btn)
        voice_btn_row.addWidget(remove_voice_btn)
        voice_btn_row.addStretch()
        voices_layout.addLayout(voice_btn_row)
        layout.addWidget(voices_group)

        presets_group = QGroupBox(self.tr('Track presets'))
        presets_layout = QVBoxLayout(presets_group)

        preset_row = QHBoxLayout()
        preset_sidebar = QVBoxLayout()
        preset_sidebar.addWidget(QLabel(self.tr('Presets')))
        self.preset_list = QListWidget()
        self.preset_list.setMaximumWidth(220)
        self.preset_list.currentRowChanged.connect(self._on_preset_selected)
        preset_sidebar.addWidget(self.preset_list)
        preset_row.addLayout(preset_sidebar)

        preset_tracks_col = QVBoxLayout()
        preset_id_row = QFormLayout()
        self.preset_id = QLineEdit()
        self.preset_id.setAccessibleName(self.tr('Preset id'))
        self.preset_id.textChanged.connect(self._on_preset_id_changed)
        preset_id_row.addRow(self.tr('Preset id'), self.preset_id)
        preset_tracks_col.addLayout(preset_id_row)
        self.track_model = TrackPresetModel(self)
        self.track_table = QTableView()
        self.track_table.setModel(self.track_model)
        configure_content_aware_columns(self.track_table, stretch_column=0)
        self.track_table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.track_table.setItemDelegateForColumn(2, DoubleSpinDelegate(-100.0, 100.0, self.track_table))
        self.track_table.setItemDelegateForColumn(3, DoubleSpinDelegate(-100.0, 100.0, self.track_table))
        preset_tracks_col.addWidget(self.track_table)

        track_btn_row = QHBoxLayout()
        add_track_btn = QPushButton(self.tr('Add track'))
        add_track_btn.clicked.connect(self._add_track)
        remove_track_btn = QPushButton(self.tr('Remove track'))
        remove_track_btn.clicked.connect(self._remove_track)
        track_btn_row.addWidget(add_track_btn)
        track_btn_row.addWidget(remove_track_btn)
        track_btn_row.addStretch()
        preset_tracks_col.addLayout(track_btn_row)
        preset_row.addLayout(preset_tracks_col, 1)
        presets_layout.addLayout(preset_row)

        preset_btn_row = QHBoxLayout()
        add_preset_btn = QPushButton(self.tr('Add preset'))
        add_preset_btn.clicked.connect(self._add_preset)
        remove_preset_btn = QPushButton(self.tr('Remove preset'))
        remove_preset_btn.clicked.connect(self._remove_preset)
        preset_btn_row.addWidget(add_preset_btn)
        preset_btn_row.addWidget(remove_preset_btn)
        preset_btn_row.addStretch()
        presets_layout.addLayout(preset_btn_row)
        layout.addWidget(presets_group, 1)

    def _wire_change_signals(self) -> None:
        self.default_lyric.textChanged.connect(self._emit_changed)
        self.preset_id.textChanged.connect(self._emit_changed)
        self.voice_model.dataChanged.connect(self._emit_changed)
        self.voice_model.rowsInserted.connect(self._emit_changed)
        self.voice_model.rowsRemoved.connect(self._emit_changed)
        self.track_model.dataChanged.connect(self._emit_changed)
        self.track_model.rowsInserted.connect(self._emit_changed)
        self.track_model.rowsRemoved.connect(self._emit_changed)

    def _emit_changed(self, *_args) -> None:
        if not self._block_change:
            self.changed.emit()

    def load_text(self, text: str) -> None:
        """Populate the form from YAML text."""
        document = parse_config_document(text)
        self.load_document(document)

    def load_document(self, document: ConfigDocument) -> None:
        """Populate the form from a structured document."""
        self._block_change = True
        try:
            self.default_lyric.setText(document.default_lyric)
            self.voice_model.set_rows(document.voices)
            self._presets = [TrackPresetRow(
                preset_id=preset.preset_id,
                tracks=[TrackConfigRow(
                    voice_id=track.voice_id,
                    track_name=track.track_name,
                    pan=track.pan,
                    volume=track.volume,
                ) for track in preset.tracks],
            ) for preset in document.track_presets]
            self._reload_preset_list(select_index=0)
        finally:
            self._block_change = False

    def to_text(self) -> str:
        """Serialize the current form state to YAML."""
        return serialize_config_document(self.to_document())

    def to_document(self) -> ConfigDocument:
        """Return the current form state as a structured document."""
        self._store_current_preset_tracks()
        return ConfigDocument(
            voices=self.voice_model.rows(),
            track_presets=list(self._presets),
            default_lyric=self.default_lyric.text().strip() or 'doo',
        )

    def _default_voice_id(self) -> str:
        voices = self.voice_model.rows()
        return voices[0].voice_id if voices else ''

    def _reload_preset_list(self, select_index: int | None = None) -> None:
        current = self.preset_list.currentRow()
        self.preset_list.blockSignals(True)
        self.preset_list.clear()
        for preset in self._presets:
            self.preset_list.addItem(QListWidgetItem(preset.preset_id))
        self.preset_list.blockSignals(False)

        if not self._presets:
            self.track_model.set_rows([])
            return

        index = select_index if select_index is not None else max(current, 0)
        index = min(index, len(self._presets) - 1)
        self.preset_list.setCurrentRow(index)
        self._load_preset_tracks(index)

    def _store_current_preset_tracks(self) -> None:
        index = self.preset_list.currentRow()
        if index < 0 or index >= len(self._presets):
            return
        preset_id = self.preset_id.text().strip()
        if preset_id:
            self._presets[index].preset_id = preset_id
            item = self.preset_list.item(index)
            if item is not None:
                item.setText(preset_id)
        self._presets[index].tracks = self.track_model.rows()

    def _on_preset_selected(self, index: int) -> None:
        if index < 0 or index >= len(self._presets):
            self.track_model.set_rows([])
            return
        self._load_preset_tracks(index)

    def _load_preset_tracks(self, index: int) -> None:
        preset = self._presets[index]
        self.preset_id.blockSignals(True)
        try:
            self.preset_id.setText(preset.preset_id)
        finally:
            self.preset_id.blockSignals(False)
        tracks = preset.tracks
        self.track_model.set_rows([
            TrackConfigRow(
                voice_id=track.voice_id,
                track_name=track.track_name,
                pan=track.pan,
                volume=track.volume,
            ) for track in tracks
        ])

    def _add_voice(self) -> None:
        self.voice_model.add_row()
        self._emit_changed()

    def _remove_voice(self) -> None:
        row = self.voice_table.currentIndex().row()
        if row < 0:
            QMessageBox.information(self, self.tr('Voice presets'), self.tr('Select a voice row to remove.'))
            return
        self.voice_model.remove_row(row)
        self._emit_changed()

    def _add_preset(self) -> None:
        self._store_current_preset_tracks()
        preset_number = len(self._presets) + 1
        default_voice = self._default_voice_id()
        self._presets.append(TrackPresetRow(
            preset_id=f'preset-{preset_number}',
            tracks=[TrackConfigRow(voice_id=default_voice)] if default_voice else [],
        ))
        self._reload_preset_list(select_index=len(self._presets) - 1)
        self._emit_changed()

    def _remove_preset(self) -> None:
        index = self.preset_list.currentRow()
        if index < 0:
            QMessageBox.information(self, self.tr('Track presets'), self.tr('Select a preset to remove.'))
            return
        del self._presets[index]
        self._reload_preset_list(select_index=max(index - 1, 0))
        self._emit_changed()

    def _add_track(self) -> None:
        self.track_model.add_row(self._default_voice_id())
        self._emit_changed()

    def _remove_track(self) -> None:
        row = self.track_table.currentIndex().row()
        if row < 0:
            QMessageBox.information(self, self.tr('Track presets'), self.tr('Select a track row to remove.'))
            return
        self.track_model.remove_row(row)
        self._emit_changed()

    def _on_preset_id_changed(self, value: str) -> None:
        index = self.preset_list.currentRow()
        if index < 0 or index >= len(self._presets):
            return
        preset_id = value.strip()
        if not preset_id:
            return
        self._presets[index].preset_id = preset_id
        item = self.preset_list.item(index)
        if item is not None:
            item.setText(preset_id)
        self._emit_changed()
