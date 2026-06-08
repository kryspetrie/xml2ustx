"""Item delegates for the custom track table."""
from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import QModelIndex
from PySide6.QtWidgets import QComboBox, QDoubleSpinBox, QStyledItemDelegate, QWidget


class VoiceIdDelegate(QStyledItemDelegate):
    """Combo-box editor for voice id column."""

    def __init__(self, voice_ids_provider: Callable[[], list[str]], parent: QWidget | None = None):
        super().__init__(parent)
        self._voice_ids_provider = voice_ids_provider

    def createEditor(self, parent: QWidget, option, index: QModelIndex) -> QWidget:  # noqa: ARG002
        combo = QComboBox(parent)
        combo.addItems(self._voice_ids_provider())
        combo.setEditable(False)
        return combo

    def setEditorData(self, editor: QWidget, index: QModelIndex) -> None:
        if isinstance(editor, QComboBox):
            value = index.model().data(index)
            if value is not None:
                editor.setCurrentText(str(value))

    def setModelData(self, editor: QWidget, model, index: QModelIndex) -> None:
        if isinstance(editor, QComboBox):
            model.setData(index, editor.currentText())


class DoubleSpinDelegate(QStyledItemDelegate):
    """Spin-box editor for numeric columns."""

    def __init__(
            self,
            minimum: float,
            maximum: float,
            parent: QWidget | None = None):
        super().__init__(parent)
        self._minimum = minimum
        self._maximum = maximum

    def createEditor(self, parent: QWidget, option, index: QModelIndex) -> QWidget:  # noqa: ARG002
        spin = QDoubleSpinBox(parent)
        spin.setRange(self._minimum, self._maximum)
        spin.setDecimals(1)
        return spin

    def setEditorData(self, editor: QWidget, index: QModelIndex) -> None:
        if isinstance(editor, QDoubleSpinBox):
            value = index.model().data(index)
            if value is not None:
                editor.setValue(float(value))

    def setModelData(self, editor: QWidget, model, index: QModelIndex) -> None:
        if isinstance(editor, QDoubleSpinBox):
            model.setData(index, editor.value())
